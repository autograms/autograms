from openai import OpenAI
import time
import tiktoken
import numpy as np
from pydantic import BaseModel

from ..memory import get_memory

import copy


client = None
embedding_client=None
api_settings = dict()
stored_tokenizers=dict()



def init_api(api_key,proxy_address=None,embedding_proxy_address=None):
    global client
    global embedding_client
    
    if proxy_address is None:

        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(base_url=proxy_address,api_key="default")
        #client = OpenAI(base_url=proxy_address)
    


    if embedding_proxy_address is None or embedding_proxy_address==proxy_address:
        embedding_client = client
    else:
         embedding_client = OpenAI(base_url=embedding_proxy_address,api_key="default")
        #client = OpenAI(base_url=proxy_address)

    if not api_key is None:
        api_settings['open_api_key']=api_key



    if not proxy_address is None:
        api_settings['openai_api_base']=proxy_address



def get_batch_embeddings(texts, model=None,**kwargs):

  
    data = embedding_client.embeddings.create(input = texts, model=model,**kwargs).data

    results = [x.embedding for x in data]
    return results

def get_single_embedding(text, model=None,**kwargs):

   result = embedding_client.embeddings.create(input = [text], model=model,**kwargs)

   return result.data[0].embedding


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

def get_tokenizer(model):
    if model in stored_tokenizers:
        tokenizer=stored_tokenizers[model]
    else:
        try:
            tokenizer =tiktoken.encoding_for_model(model)
        except:
            try:
                from transformers import AutoTokenizer
                try:
                    
                    tokenizer = AutoTokenizer.from_pretrained(model)
                 #   print(f"Found huggingface tokenizer for {model}")
                except:
                #    print(f"tokenizer not found for {model}, using openai tokenizer for prompt length enforcement")
                    tokenizer = tiktoken.encoding_for_model("gpt-4o")
                    
            except:
               # print(f"tokenizer not found for {model}, using openai tokenizer for prompt length enforcement")
                tokenizer = tiktoken.encoding_for_model("gpt-4o")
                #raise Exception(f"{model} not found. If this is a transformers model, you need to do `pip install transformers` to allow the tokenizer to be found. If this is a valid openai model, then your tiktoken installation may be out of date. If this is a neither an openai or transfomers model, your model may not have a tokenizer, which is necessary for certain autograms functions. future versions of autograms may provide a workaround.")

                #raise Exception(f"{model} not found. If this is a valid openai model, then your tiktoken installation may be out of date. If this is a neither an openai or transfomers model, your model may not have a tokenizer, which is necessary for certain autograms functions. Future versions of autograms may provide a workaround.")

    stored_tokenizers[model]=tokenizer
    return tokenizer

def get_chatbot_messages_single(text,system_prompt=None,truncate=True,model=None,system_prompt_in_turns=False,multi_modal_inputs=None):
    memory = get_memory()
    config = memory.config
    if model is None:
        model = config.chatbot_path

    tokenizer=get_tokenizer(model)

    if truncate:
        max_len=config.chatbot_max_input_len

        if not system_prompt is None:
            system_tokens = tokenizer.encode(system_prompt)
            if len(system_tokens)>max_len:
                print(f"warning system prompt is too long({len(system_tokens)} tokens). It is only allowed to be half of config.chatbot_max_input_len, which is set to {config.classifier_max_input_len} tokens. truncating system prompt.")
                system_prompt = tokenizer.decode(system_tokens[:int(max_len/2)])+"..."

            max_len = max_len-len(tokenizer.encode(system_prompt))


        tokens = tokenizer.encode(text)
        if len(tokens)>max_len:
            new_tokens = tokens[-max_len:]
            text=tokenizer.decode(new_tokens)
    messages=[]
    if not system_prompt is None:
        if not system_prompt_in_turns:
            messages.append({"role":"system", "content":[{"type": "text", "text":system_prompt}] })
        else:
            text=system_prompt+"\n\n"+text
        
    messages.append({"role":"user", "content": [{"type": "text", "text":text}]})

    if not multi_modal_inputs is None:
        for turn in multi_modal_inputs:
            messages[-1]['content'].append(turn)

    return messages
def get_classifier_messages(input_turns,output_turns,system_prompt,system_prompt_in_turns=False,truncate_input=False,model=None,multi_modal_inputs=None):
    memory = get_memory()
    config=memory.config

    if model is None:
        model = config.classifier_path

    tokenizer=get_tokenizer(model)


    if truncate_input:
        max_input_length = config.classifier_max_input_len
        system_tokens = tokenizer.encode(system_prompt)
        if len(system_tokens)>max_input_length/2:
            print(f"warning system prompt is too long({len(system_tokens)} tokens). It is only allowed to be half of config.chatbot_max_input_len, which is set to {config.chatbot_max_input_len} tokens. truncating system prompt.")
            system_prompt = tokenizer.decode(system_tokens[:int(max_input_length/2)])+"..."

        max_input_length = max_input_length-len(tokenizer.encode(system_prompt))


        input_turns,output_turns=truncate_turn_input(input_turns,output_turns,tokenizer,max_input_length)



    
    messages=[]
    if not system_prompt is None:
    
        if system_prompt_in_turns:
             input_turns[0] = system_prompt+"\n\n"+input_turns[0]
        else:
            messages.append({"role":"system", "content": [{"type": "text", "text":system_prompt}]})
    for i in range(len(output_turns)):
        messages.append({"role":"user", "content": [{"type": "text", "text":input_turns[i]}]})
        messages.append({"role":"assistant", "content": [{"type": "text", "text":output_turns[i]}]})

    messages.append({"role":"user", "content": [{"type": "text", "text":input_turns[-1]}]})
    if not multi_modal_inputs is None:
        for turn in multi_modal_inputs:
            messages[-1]['content'].append(turn)

    return messages

def truncate_prompt(prompt,model=None,max_input_length=None):
    memory = get_memory()
    config=memory.config
    if model is None:
        model = config.chatbot_path
    tokenizer=get_tokenizer(model)
    if max_input_length is None:
        max_input_length = config.chatbot_max_input_len

    tokens = tokenizer.encode(prompt)
    if len(tokens)>max_input_length:
        prompt = tokenizer.decode(tokens[-max_input_length:])
    return prompt



def get_chatbot_messages(input_turns,output_turns,system_prompt,system_prompt_in_turns=False,truncate_input=False,model=None,multi_modal_inputs=None):
    memory = get_memory()
    config=memory.config

    if model is None:
        model = config.chatbot_path

    tokenizer=get_tokenizer(model)


    if truncate_input:
        max_input_length = config.chatbot_max_input_len
        system_tokens = tokenizer.encode(system_prompt)
        if len(system_tokens)>max_input_length/2:
            print(f"warning system prompt is too long({len(system_tokens)} tokens). It is only allowed to be half of config.chatbot_max_input_len, which is set to {config.chatbot_max_input_len} tokens. truncating system prompt.")
            system_prompt = tokenizer.decode(system_tokens[:int(max_input_length/2)])+"..."

        max_input_length = max_input_length-len(tokenizer.encode(system_prompt))


        input_turns,output_turns=truncate_turn_input(input_turns,output_turns,tokenizer,max_input_length)



    
    messages=[]
    if not system_prompt is None:
    
        if system_prompt_in_turns:
             input_turns[0] = system_prompt+"\n\n"+input_turns[0]
        else:
            messages.append({"role":"system", "content": [{"type": "text", "text":system_prompt}]})
    for i in range(len(output_turns)):
        messages.append({"role":"user", "content": [{"type": "text", "text":input_turns[i]}]})
        messages.append({"role":"assistant", "content": [{"type": "text", "text":output_turns[i]}]})

    messages.append({"role":"user", "content": [{"type": "text", "text":input_turns[-1]}]})
    if not multi_modal_inputs is None:
        for turn in multi_modal_inputs:
            messages[-1]['content'].append(turn)

    return messages



def call_openai_completions(messages=None,prompt=None,handle_errors=False,handle_refusal=False,model=None,ignore_config=False,prefix="",**kwargs):
    
    if not ignore_config:
        memory = get_memory()
        config=memory.config

        test_mode = memory.test_mode
    generation_args = copy.deepcopy(kwargs)
    for arg in config.chatbot_generation_args:
        if not arg in generation_args:
            generation_args[arg]= config.chatbot_generation_args[arg]
    if not "max_tokens" in generation_args:
        generation_args["max_tokens"] = config.max_tokens
    if not 'n' in generation_args:
        generation_args['n']=1
    if model is None:
        model = config.chatbot_path

    if client is None:
        raise Exception("Open AI APIs not initialized. This is supposed to happen when autogram is defined.") 
    
    tokenizer=get_tokenizer(model)

    if prompt is None:
        new_messages = []
        for message in messages:
            role = message['role']
            if type(message['content'])==list:
                text = message['content'][0]['text']
            else:
                text = message['content']
            new_messages.append({"role":role,"content":text})


        formatted_prompt = tokenizer.apply_chat_template(new_messages,tokenize=False)
        formatted_prompt +="<|Assistant|>"+prefix
        prompt = formatted_prompt

    
    #result = client.completions.create(model=model,prompt=prompt,**generation_args)
    result = completions_with_backoff(model,prompt,generation_args,config)
    

    responses = [prefix+result.choices[i].text for i in range(generation_args['n'])]
    
    usage_log = result.usage.to_dict()
    usage_log['model'] = model


    return responses[0],usage_log


    

def completions_classifier(allowed_tokens,messages=None,prompt=None,give_logits=False,handle_errors=False,handle_refusal=False,model=None,ignore_config=False,prefix="",**kwargs):
    
    memory = get_memory()
    config=memory.config    
    if model is None:
        model = config.chatbot_path
    memory = get_memory()
    config=memory.config
    tokenizer=get_tokenizer(model)

    test_mode = memory.test_mode
    if prompt is None:
        new_messages = []
        for message in messages:
            role = message['role']
            if type(message['content'])==list:
                text = message['content'][0]['text']
            else:
                text = message['content']
            new_messages.append({"role":role,"content":text})


        formatted_prompt = tokenizer.apply_chat_template(new_messages,tokenize=False)
        formatted_prompt +="<|Assistant|>"+prefix
        prompt = formatted_prompt
    answer_dict = dict()

    
    for i in range(len(allowed_tokens)):


        if isinstance(tokenizer, tiktoken.Encoding):
            answer = allowed_tokens[i]
            token=tokenizer.encode(answer)
            answer_dict[str(token[0])]=100

        else:

            answer = allowed_tokens[i]
            token=tokenizer.encode(prompt+answer)[-1]
            if token == tokenizer.eos_token_id:
                token=tokenizer.encode(prompt+answer)[-2]


            answer_dict[str(token)]=100
            

            #answer_dict[token[-1]]=100

        num_logprobs=len(answer_dict)
 


           
    kwargs["logit_bias"]=answer_dict
    generation_args = copy.deepcopy(kwargs)
    for arg in config.chatbot_generation_args:
        if not arg in generation_args:
            generation_args[arg]= config.chatbot_generation_args[arg]
    #if not "max_tokens" in generation_args:
    generation_args["max_tokens"] = 1
    #if not 'n' in generation_args:
    generation_args['n']=1
    if give_logits:
        generation_args['logprobs'] = num_logprobs
    if model is None:
        model = config.chatbot_path

    if client is None:
        raise Exception("Open AI APIs not initialized. This is supposed to happen when autogram is defined.") 
    

    generation_args['temperature']=0.0


    
    #result = client.completions.create(model=model,prompt=prompt,**generation_args)
    result = completions_with_backoff(model,prompt,generation_args,config)
    


    if give_logits:
     #   log_probs = result.choices[0].logprobs.content[0].top_logprobs
        log_probs = result.choices[0].logprobs.top_logprobs[0]


        dict_mapping = {x.replace(" ",""):y for x,y in list(zip(log_probs.keys(),log_probs.values()))},  #{x['token']:x.logprob for x in log_probs}
        logits = []
        for answer in allowed_tokens:
            if answer in dict_mapping:
                logits.append(dict_mapping[answer])
            else:
                if answer == result.choices[0].text:
                    logits.append(0)
                else:
                    logits.append(-100)
        output = logits
    else:
        output = result.choices[0].text.replace(" ","")
      

   # import pdb;pdb.set_trace()
  #  responses = [prefix+result.choices[i].text for i in range(generation_args['n'])]
    
    usage_log = result.usage.to_dict()
    usage_log['model'] = model
    


    return output,usage_log
    

    


    
def call_openai_chatbot(messages,handle_errors=False,handle_refusal=False,model=None,ignore_config=False,**kwargs):
    
    if not ignore_config:
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

    tokenizer=get_tokenizer(model)


    for arg in config.chatbot_generation_args:
        if not arg in generation_args:
            generation_args[arg]= config.chatbot_generation_args[arg]
    if not "max_tokens" in generation_args:
        generation_args["max_tokens"] = config.max_tokens


    if "o1" in model:
     #   generation_args["max_completion_tokens"]=generation_args["max_tokens"]
        del generation_args["max_tokens"]
        if "temperature" in generation_args:
            del generation_args["temperature"]
    



    if not 'n' in kwargs:
        kwargs['n']=1


    if test_mode:
        
        texts = ["<test mode enabled, no response available.>"]*kwargs['n']
        

        success=True
        usage_log = {'model':'test'}

        return texts,usage_log
    else:
        num_errors=0
        num_refusals=0
        success=False

        result = chat_completions_with_backoff(model=model,messages=messages,generation_args=generation_args,config=config)

        usage_log = result.usage.to_dict()
        usage_log['model'] = model
        responses = [result.choices[i].message.content for i in range(kwargs['n'])]

        return responses[0],usage_log

        # while num_errors+num_refusals<config.chatbot_max_tries:
        #     if handle_errors:
        #         try:
        #             result = client.chat.completions.create(model=model,messages=messages,**generation_args)
        #             usage_log = result.usage.to_dict()
        #             usage_log['model'] = model
        #         except:
        #             num_errors+=1
        #             responses=[config.error_response]*kwargs['n']
        #             usage_log = {'model':'failed'}
        #             continue
        #     else:
        #         result = client.chat.completions.create(model=model,messages=messages,**generation_args)



        #     responses = [result.choices[i].message.content for i in range(kwargs['n'])]
        #     if handle_refusal:
        #         is_refusal=detect_refusal(responses[0])

        #         if is_refusal:
        #             num_refusals+=1
        #             generation_args = refusal_args(responses[0],tokenizer,generation_args)

        #             continue
        #     success=True
        #     break
       
        

        


def chat_completions_with_backoff(model,messages,generation_args,config):
    sleep_time=5
    for i in range(config.chatbot_max_tries):
        
        try:
            result = client.chat.completions.create(model=model,messages=messages,**generation_args)
        except:
            time.sleep(sleep_time)
            sleep_time*=2
    return result

def formatted_chat_completions_with_backoff(model,messages,response_format,generation_args,config):

    for i in range(config.chatbot_max_tries):
        sleep_time = 5
        try:
           result = client.beta.chat.completions.parse(
                messages=messages,
                model=model,
                response_format=response_format,
                **generation_args
            )
        except:
            time.sleep(sleep_time)
            sleep_time*=2
    return result

def completions_with_backoff(model,prompt,generation_args,config):

    for i in range(config.chatbot_max_tries):
        sleep_time = 5
        try:
           result = client.completions.create(model=model,prompt=prompt,**generation_args)
        except:
            time.sleep(sleep_time)
            sleep_time*=2
    return result



    


def call_openai_chat_formatted(messages,obj_structure=None,model=None,**kwargs):
    
    
    memory = get_memory()
    config=memory.config
        
    if model is None:
        model = config.chatbot_path

    generation_args = copy.deepcopy(kwargs)

    for arg in config.chatbot_generation_args:
        if not arg in generation_args:
            generation_args[arg]= config.chatbot_generation_args[arg]
    num_tries = 2
    for i in range(num_tries):
        try:

           # print(generation_args)
            # result = client.beta.chat.completions.parse(
            #     messages=messages,
            #     model=model,
            #     response_format=obj_structure,
            #     **generation_args
            # )
            result = formatted_chat_completions_with_backoff(model,messages,obj_structure,generation_args,config)
            #print("got result")
            usage_log = result.usage.to_dict()
            usage_log['model'] = model

            output_obj = result.choices[0].message
    

            if output_obj.parsed:
                
                output = output_obj.parsed
                raw_str = result.choices[0].message.content
                success=True


            else:
                
                #if isinstance(obj_structure,dict)
                    
                raw_str = result.choices[0].message.content
                output = raw_str
                
                if output_obj.refusal:
                    success=False
                else:
                    success=True
            if success:
                break



        except Exception as e:

            print(e)
            if i<num_tries-1:
                continue
            print("Warning!!!! failed to parse openai structured output,object will be generated to defaults")

            return None,None,{'model':'failed'}


  
    return output,raw_str, usage_log


# def call_openai_json_classifier(messages,obj_structure=None,model=None,**kwargs):
    
    
#     memory = get_memory()
#     config=memory.config

#     kwargs["temperature"]=0.0
#     kwargs["n"]=1

#     if return_logits:


#         kwargs["logprobs"]=True
#         kwargs["top_logprobs"]= 20
#     try:


#         result = client.beta.chat.completions.parse(
#             messages=messages,
#             model=model,
#             response_format=obj_structure,
#             **kwargs
#         )
#         usage_log = result.usage.to_dict()
#         usage_log['model'] = model

#         output_obj = result.choices[0].message
  

#         if output_obj.parsed:
            
#             output = output_obj.parsed
#             raw_str = result.choices[0].message.content
#             success=True


#         else:
            
#             #if isinstance(obj_structure,dict)
                
#             raw_str = result.choices[0].message.content
#             output = raw_str
            
#             if output_obj.refusal:
#                 success=False
#             else:
#                 success=True



#     except Exception as e:
#         print(e)
#         print("Warning!!!! failed to parse openai structured output,object will be generated to defaults")
#         return None,None,{'model':'failed'}


  
#     return output,raw_str, usage_log



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

def orig_get_classifier_messages(text,truncate=True,model=None,system_prompt=None,system_prompt_in_turns=False,multi_modal_inputs=None):
    memory = get_memory()
    config = memory.config
    if model is None:
        model = config.classifier_path

    tokenizer=get_tokenizer(model)

    if truncate:
        max_len=config.classifier_max_input_len

        if not system_prompt is None:
            system_tokens = tokenizer.encode(system_prompt)
            if len(system_tokens)>max_len:
                print(f"warning system prompt is too long({len(system_tokens)} tokens). It is only allowed to be half of config.chatbot_max_input_len, which is set to {config.classifier_max_input_len} tokens. truncating system prompt.")
                system_prompt = tokenizer.decode(system_tokens[:int(max_len/2)])+"..."

            max_len = max_len-len(tokenizer.encode(system_prompt))


        tokens = tokenizer.encode(text)
        if len(tokens)>max_len:
            new_tokens = tokens[-max_len:]
            text=tokenizer.decode(new_tokens)
    messages=[]
    if not system_prompt is None:
        if not system_prompt_in_turns:
            messages.append({"role":"system", "content":[{"type": "text", "text":system_prompt}] })
        else:
            text=system_prompt+"\n\n"+text
        
    messages.append({"role":"user", "content": [{"type": "text", "text":text}]})

    if not multi_modal_inputs is None:
        for turn in multi_modal_inputs:
            messages[-1]['content'].append(turn)

    return messages

def call_openai_classifier(messages,answer_choices,model=None,class_biases=None,return_logits=False,**kwargs):
        memory = get_memory()
        config = memory.config
        # if "model" in kwargs:
        #     model=kwargs["model"]
        #     del kwargs["model"]
        # else:
        #     model = config.chatbot_path


        if model is None:
            model = config.classifier_path

        tokenizer =get_tokenizer(model)

        answer_dict=dict()

        """
        logit biases are used to prevent model from generating token outside of the answer choices
        """
      
        if not class_biases is None:
            class_biases = np.array(class_biases) -np.max(class_biases)

        for i in range(len(answer_choices)):
            answer = answer_choices[i]
            token=tokenizer.encode(answer)

            if isinstance(tokenizer, tiktoken.Encoding):
                if class_biases is None:
                    answer_dict[str(token[0])]=100
                else:
                    answer_dict[str(token[0])]=int(100+class_biases[i])
            else:
                if class_biases is None:
                    answer_dict[token[-1]]=100
                else:
                    answer_dict[token[-1]]=int(100+class_biases[i])         
     
        if return_logits:
            if memory.test_mode:
                logits = np.random.randn(len(answer_dict))
                result=logits
                usage_log = {'model':'test'}

            else:

                kwargs["logit_bias"]=answer_dict
                kwargs["temperature"]=0.0
                kwargs["max_tokens"]=1
                kwargs["n"]=1
                kwargs["logprobs"]=True
                kwargs["top_logprobs"]= 20


                try:

                    #response = client.chat.completions.create(model=model,messages=messages,**kwargs)
                    result = chat_completions_with_backoff(model=model,messages=messages,generation_args=kwargs,config=config)
                    usage_log = response.usage.to_dict()
                    usage_log['model'] = model
                    log_probs = response.choices[0].logprobs.content[0].top_logprobs

                    dict_mapping = {x.token:x.logprob for x in log_probs}
                    logits = []
                    for answer in answer_choices:
                        if answer in dict_mapping:
                            logits.append(dict_mapping[answer])
                        else:
                            if answer == response.choices[0].message.content:
                                logits.append(0)
                            else:
                                logits.append(-100)

                    result = logits
                  
                except Exception as e:

                    logits = np.random.randn(len(answer_dict))
                    result = logits
                    print(e)
                    usage_log = {'model':'failed'}
                    print("Warning, open ai classifier failed")


        else:


            if memory.test_mode:
                pred_ind = np.random.choice(len(answer_choices),p=[1/len(answer_choices)]*len(answer_choices))
                success=True
                result =  answer_choices[pred_ind]
                usage_log = {'model':'test'}
            else:
                #try:
           
                kwargs["logit_bias"]=answer_dict
                kwargs["temperature"]=0.0
                kwargs["max_tokens"]=1
                kwargs["n"]=1
            

                #response = client.chat.completions.create(model=model,messages=messages,**kwargs)
                response = chat_completions_with_backoff(model=model,messages=messages,generation_args=kwargs,config=config)
                usage_log = response.usage.to_dict()
                usage_log['model'] = model
            
                result = response.choices[0].message.content


        return result,usage_log


        

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




    



