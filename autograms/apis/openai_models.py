from openai import OpenAI
import time
import tiktoken
import numpy as np
from pydantic import BaseModel

from ..memory import get_memory

import copy


# openai_version = pkg_resources.get_distribution("openai").version

# legacy_openai= [int(x) for x in openai_version.split('.')][0]==0


client = None



def init_api(api_key):
    global client
    client = OpenAI(api_key=api_key)

   

# def get_tokenizer(model):
#     if model in tokenizers:
#         return tokenizers[model]
#     else:
#         tokenizer = tiktoken.encoding_for_model(model)
#         tokenizers[model]=tokenizer

#         return tokenizer
    


def get_batch_embeddings(texts, model="text-embedding-3-small"):

   data = client.embeddings.create(input = texts, model=model).data
   results = [x.embedding for x in data]
   return results

def get_single_embedding(text, model="text-embedding-3-small"):

   result = client.embeddings.create(input = [text], model=model).data[0].embedding
   return result


def truncate_turn_input(inputs,outputs,tokenizer,max_input_len):
    


    input_lens=[0]*len(inputs)
    output_lens = [0]*len(outputs)

    
    

    for i in range(len(inputs)):
        input_lens[i] = len(tokenizer.encode(inputs[i]))+5

    for i in range(len(outputs)):
        output_lens[i] = len(tokenizer.encode(outputs[i]))+5

    prefix_len=0
  

    total_len = prefix_len+np.sum(output_lens)+np.sum(input_lens)
    if total_len>max_input_len:
        while len(inputs)>1:
            inputs = inputs[1:]
            outputs = outputs[1:]
            input_lens = [input_lens[0]]+input_lens[2:]
            output_lens = output_lens[1:] #+input_lens[2:]
            total_len = prefix_len+np.sum(output_lens)+np.sum(input_lens)

            if total_len<max_input_len:
                print(total_len)
                break
        if total_len>max_input_len:
            prefix=""
            total_len = np.sum(input_lens)
            if total_len>max_input_len:
                inputs[0] = tokenizer.decode(tokenizer.encode(inputs[0])[-max_input_len:])

    return inputs,outputs



# def call_openai_formatted(input_turns,output_turns,system_prompt=None,handle_errors=False,handle_refusal=False,truncate_input=True,**kwargs):
#     config = get_memory().config
#     if "model" in kwargs:
#         model=kwargs["model"]
#     else:
#         model =config.chatbot_path



#     #tokenizer = autogram.get_tokenizer("openai",model)

#     if truncate_input:
#         input_turns,output_turns=truncate_input(input_turns,output_turns)


def get_chatbot_messages(input_turns,output_turns,system_prompt,system_prompt_in_turns=False,truncate_input=False,model=None):
    memory = get_memory()
    config=memory.config

    if model is None:
        model = config.chatbot_path
    tokenizer =tiktoken.encoding_for_model(model)

    if truncate_input:
        max_input_length = config.chatbot_max_input_len

        input_turns,output_turns=truncate_turn_input(input_turns,output_turns,tokenizer,max_input_length)
    
    messages=[]
    if not system_prompt is None and not system_prompt_in_turns:
        messages.append({"role":"system", "content": system_prompt})
    for i in range(len(output_turns)):
        messages.append({"role":"user", "content": input_turns[i]})
        messages.append({"role":"assistant", "content": output_turns[i]})

    messages.append({"role":"user", "content": input_turns[-1]})

    if not system_prompt is None and not system_prompt_in_turns:
        messages[0]['content'] = system_prompt+"\n\n"+messages[0]['content']
    return messages

def call_openai_chatbot(messages,handle_errors=False,handle_refusal=False,model=None,**kwargs):
    
    memory = get_memory()
    config=memory.config

    test_mode = memory.test_mode
    
    if client is None:
        raise Exception("Open AI APIs not initialized. This is supposed to happen when autogram is defined.") 
    
    generation_args = copy.deepcopy(kwargs)
    # if "model" in generation_args:
    #     model=generation_args["model"]
    if model is None:
        model = config.chatbot_path

    tokenizer =tiktoken.encoding_for_model(model)

    if not "temperature" in generation_args:
        generation_args["temperature"] = config.chatbot_generation_args['temperature']
    if not "max_tokens" in generation_args:
        generation_args["max_tokens"] = config.max_response_len



    if not 'n' in kwargs:
        kwargs['n']=1


    if test_mode:
        
        texts = ["<test mode enabled, no response available.>"]*kwargs['n']
        

        success=True

        return texts,success
    else:
        num_errors=0
        num_refusals=0
        success=False

        while num_errors+num_refusals<config.chatbot_max_tries:
            if handle_errors:
                try:
                    result = client.chat.completions.create(model=model,messages=messages,**generation_args)
                except:
                    num_errors+=1
                    responses=[config.error_response]*kwargs['n']
                    continue
            else:
                result = client.chat.completions.create(model=model,messages=messages,**generation_args)
            responses = [result.choices[i].message.content for i in range(kwargs['n'])]
            if handle_refusal:
                is_refusal=detect_refusal(responses[0])

                if is_refusal:
                    num_refusals+=1
                    generation_args = refusal_args(responses[0],tokenizer,generation_args)

                    continue
            success=True
            break

        return responses,success


def call_openai_chat_formatted(messages,obj_structure=None,model=None,**kwargs):
    
    
    memory = get_memory()
    config=memory.config

    if model is None:
        model = config.chatbot_path



    try:
        result = client.beta.chat.completions.parse(
            messages=messages,
            model=model,
            response_format=obj_structure,
            **kwargs
        )

        output_obj = result.choices[0].message

        if output_obj.parsed:
            
            output = output_obj.parsed
            raw_str = result.choices[0].message.content
            success=True


        else:
        
            
            raw_str = result.choices[0].message.content
            output = raw_str
            success=False

    except Exception as e:
        print(e)
        print("Warning!!!! failed to parse openai structured output,object will be generated to defaults")
        return None,None,False




    return output,raw_str, success



def call_openai_chat_completions(**kwargs):

    result = client.chat.completions.create(
        **kwargs
    )
    return result

def detect_refusal(response,banned_phrases):
    passed_response=True
    for phr in banned_phrases:
        if phr.lower() in response.lower():
            passed_response=False

    return not passed_response

def refusal_args(response,tokenizer,generation_args):
    logit_bias=dict()
    all_tokens = []
   
    all_tokens+= tokenizer.encode(response)

    all_tokens = set(all_tokens)
    for token in all_tokens:
        logit_bias[str(token)]=-1


    generation_args['logit_bias']=logit_bias
    
    if 'temperature' in generation_args:

        if generation_args['temperature']<0.4:
            generation_args['temperature']=0.4
        elif generation_args['temperature']<2:
            generation_args['temperature']*=1.5
    else:
        generation_args['temperature']=1

    return generation_args



# def call_chat_completions(model,messages,handle_refusal,**kwargs):

#     result = client.chat.completions.create(
#         model=model,
#         messages=messages,
#         temperature=temperature,
#         **input_args
#     )

def get_classifier_messages(text,truncate=True,model=None):
    memory = get_memory()
    config = memory.config
    if model is None:
        model = config.classifier_path
    tokenizer = tiktoken.encoding_for_model(model)

    if truncate:
        max_len=config.classifier_max_input_len
        tokens = tokenizer.encode(text)
        if len(tokens)>max_len:
            new_tokens = tokens[-max_len:]
            text=tokenizer.decode(new_tokens)

    messages = [{"role":"user", "content": text}]

    return messages

def call_openai_classifier(messages,answer_choices,model=None,class_biases=None,**kwargs):
        memory = get_memory()
        config = memory.config
        # if "model" in kwargs:
        #     model=kwargs["model"]
        #     del kwargs["model"]
        # else:
        #     model = config.chatbot_path

        if model is None:
            model = config.classifier_path


        tokenizer =tiktoken.encoding_for_model(model)

        answer_dict=dict()

        """
        logit biases are used to prevent model from generating token outside of the answer choices
        """

        if not class_biases is None:
            class_biases = np.array(class_biases) -np.max(class_biases)

        for i in range(len(answer_choices)):
            answer = answer_choices[i]
            token=tokenizer.encode(answer)
            if class_biases is None:
                answer_dict[str(token[0])]=100
            else:
                answer_dict[str(token[0])]=int(100+class_biases[i])


        if memory.test_mode:
            pred_ind = np.random.choice(len(answer_choices),p=[1/len(answer_choices)]*len(answer_choices))
            success=True
            return answer_choices[pred_ind],success
        else:

            kwargs["logit_bias"]=answer_dict
            kwargs["temperature"]=0.0
            kwargs["max_tokens"]=1
            kwargs["n"]=1

            response = client.chat.completions.create(model=model,messages=messages,**kwargs)

          

            return response.choices[0].message.content,True



        

def generate_image(prompt,model="dall-e-3",size="1024x1024",**kwargs):


    
    image = client.images.generate(
    model=model,
    prompt=prompt,
    n=1,
    size=size,
    **kwargs
    )
    return image.data[0]



# class OpenAImodel(LLM):

#     def __init__(self):


#         autogram = get_autogram





#         if "openai" in autogram.api_keys.keys():
#             if legacy_openai:
#                 self.client = openai
#                 self.client.api_key = api_keys["openai"]
#             else:
#                 from openai import OpenAI
#                 self.client =  OpenAI(api_key=api_keys["openai"])
#         else:
#             raise Exception("missing Open AI API key") 
        
#         # self.generation_args=autogramconfig.chatbot_generation_args
#         # self.max_input_len = autogram_config.chatbot_max_input_len
#         # self.model_name=autogram_config.chatbot_path
#         # self.max_tries=autogram_config.chatbot_max_tries
#         # self.wait_per_try=autogram_config.chatbot_wait_per_try
#         # self.banned_phrases=autogram_config.banned_phrases
#         # self.error_response= autogram_config.error_response
#         self.default_model = autogram.config.chatbot_path

#     def truncate_input(self,inputs,outputs,prefix,**kwargs):
        


#         input_lens=[0]*len(inputs)
#         output_lens = [0]*len(outputs)

#         tokenizer = self.autogram.get_tokenzier()
        

#         for i in range(len(inputs)):
#             input_lens[i] = len(self.tokenizer.encode(inputs[i]))+5

#         for i in range(len(outputs)):
#             output_lens[i] = len(self.tokenizer.encode(outputs[i]))+5
#         if prefix is None or len(prefix)==0:
#             prefix_len=0
#         else:
#             prefix_len =  len(self.tokenizer.encode(prefix))

#         total_len = prefix_len+np.sum(output_lens)+np.sum(input_lens)
#         if total_len>self.max_input_len:
#             while len(inputs)>1:
#                 inputs = [inputs[0]]+inputs[2:]
#                 outputs = outputs[1:]
#                 input_lens = [input_lens[0]]+input_lens[2:]
#                 output_lens = output_lens[1:] #+input_lens[2:]
#                 total_len = prefix_len+np.sum(output_lens)+np.sum(input_lens)

#                 if total_len<self.max_input_len:
#                     print(total_len)
#                     break
#             if total_len>self.max_input_len:
#                 prefix=""
#                 total_len = np.sum(input_lens)
#                 if total_len>self.max_input_len:
#                     inputs[0] = self.tokenizer.decode(self.tokenizer.encode(inputs[0])[-self.max_input_len:])

#         return inputs,outputs,prefix


#     def generate_reply(self, inputs,outputs):

#         messages=[]
#         for i in range(len(outputs)):
#             messages.append({"role":"user", "content": inputs[i]})
#             messages.append({"role":"assistant", "content": outputs[i]})

#         messages.append({"role":"user", "content": inputs[-1]})


#         if self.test_mode:
#             if ['batch_size'] in self.generation_args:
#                 texts = ["<test mode enabled, no response available.>"]*self.generation_args['batch_size']
#             else:
#                 texts = ["<test mode enabled, no response available.>"]

#             success=True


#         else:
        
#             texts,success = self.get_responses_conv(messages)


#         return texts,success
    
#     def process_generation_args(self,generation_args):
#         new_args=dict()
#         if "batch_size" in generation_args.keys():

#             new_args['n'] = generation_args["batch_size"]
#         else:
#             new_args['n'] = 1

#         if "max_tokens" in generation_args.keys():
        
#             new_args['max_tokens'] = generation_args["max_tokens"]
#         else:
#             new_args['max_tokens'] = 512


#         return new_args




        
#     def get_responses_conv(self,messages):

#         if "temperature" in self.generation_args.keys():
#             temperature = self.generation_args["temperature"]
#         else:
#             print("WARNING. Temperature not set, manually setting temperature")
#             temperature=0.7


#         num_tokens = count_tokens(messages,self.tokenizer)

#         print("num_tokens: "+str(num_tokens))




#         input_args = self.process_generation_args(self.generation_args)



#         for i in range(self.max_tries):

#             try:
            

#                 if legacy_openai:
#                     response = self.client.ChatCompletion.create(
#                         model=self.model_name,
#                         messages=messages,
#                         temperature=temperature,
#                         **input_args
#                     )
                
#                     responses = [response.choices[i]['message']['content'] for i in range(input_args['n'])]


#                 else:
#                     response = self.client.chat.completions.create(
#                         model=self.model_name,
#                         messages=messages,
#                         temperature=temperature,
#                         **input_args
#                     )
                


#                     responses = [response.choices[i].message.content for i in range(input_args['n'])]
                

#                 if len(self.banned_phrases)>0 and i < (self.max_tries-1):
#                     passed=False
#                     for resp in responses:
#                         passed_response=True
#                         for phr in self.banned_phrases:
#                             if phr.lower() in resp.lower():
#                                 passed_response=False

#                         #we just need one response to pass
#                         if passed_response:
#                             passed=True
#                     if not passed:
#                         """
#                         Handling of banned phrases. If response generated banned phrases, we use the logit bias to downweight the whole respond.
#                         Usually banned phrases are when model refuses to reply (ex: I'm sorry, I can't do that.)
#                         This most commonly happens when it is ignoring an instruction we are giving it, common when simulating the user.
#                         """
                        
#                         print("Generation iteration " +str(i) + " from Open AI didn't satisfy requirements, likely because it refused to follow instruction, regenerating with penalty.")
#                         logit_bias=dict()
#                         all_tokens = []
#                         for resp in responses:
#                             all_tokens+=self.tokenizer.encode(resp)

#                         all_tokens = set(all_tokens)
#                         for token in all_tokens:
#                             logit_bias[str(token)]=-2


#                         input_args['logit_bias']=logit_bias
                        

#                         if temperature<0.4:
#                             temperature=0.4
#                         else:
#                             temperature*=1.5
#                         time.sleep(self.wait_per_try)

                
#                         continue

                

#                 return responses,True
#             except Exception as exception_str:
#                 print("Genetation iteration " +str(i) +" gave the following exception "+str(exception_str) +"\n")
            
#         print("Warning, open ai response generation error!!!!!!!!!!!!!!!!!!!!!!")
#         return [self.error_response]*input_args['n'],False
    

# def count_tokens(messages,encoding):
#     tokens_per_message = 4
#     tokens_per_name = 1
#     num_tokens = 0
#     for message in messages:
#         num_tokens += tokens_per_message
#         for key, value in message.items():
#             num_tokens += len(encoding.encode(value))
#             if key == "name":
#                 num_tokens += tokens_per_name
#     num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
#     return num_tokens




    



