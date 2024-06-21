import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from .chatbot import Chatbot
import numpy as np
import time

class HuggingfaceChatbot(Chatbot):
    def __init__(self,autogram_config,api_keys=None,chatbot=None):


        super().__init__(autogram_config)


        self.generation_args=autogram_config.chatbot_generation_args
        if chatbot is None:
            self.tokenizer = AutoTokenizer.from_pretrained(autogram_config.chatbot_path)
            self.model=AutoModelForCausalLM.from_pretrained(autogram_config.chatbot_path,torch_dtype=torch.float16)
            self.model.to("cuda:0")
        else:
            #share model objects with other bots
            self.tokenizer=chatbot.tokenizer
            self.model=chatbot.model


        

        
        self.max_input_len = autogram_config.chatbot_max_input_len
        self.max_tries=autogram_config.chatbot_max_tries
        self.wait_per_try=autogram_config.chatbot_wait_per_try
        self.banned_phrases=autogram_config.banned_phrases
        self.error_response= autogram_config.error_response


        self.test_mode = False
        
        

    def truncate_input(self,inputs,outputs,prefix):
        


        input_lens=[0]*len(inputs)
        output_lens = [0]*len(outputs)
        

        for i in range(len(inputs)):
            input_lens[i] = len(self.tokenizer.encode(inputs[i]))

        for i in range(len(outputs)):
            output_lens[i] = len(self.tokenizer.encode(outputs[i]))
        if prefix is None or len(prefix)==0:
            prefix_len=0
        else:
            prefix_len =  len(self.tokenizer.encode(prefix))

        total_len = prefix_len+np.sum(output_lens)+np.sum(input_lens)
        if total_len>self.max_input_len:
            while len(inputs)>1:
                inputs = [inputs[0]]+inputs[2:]
                outputs = outputs[1:]
                input_lens = [input_lens[0]]+input_lens[2:]
                output_lens = output_lens[1:] #+input_lens[2:]
                total_len = prefix_len+np.sum(output_lens)+np.sum(input_lens)

                if total_len<self.max_input_len:
                    break
            if total_len>self.max_input_len:
                prefix=""
                total_len = np.sum(input_lens)
                if total_len>self.max_input_len:
                    inputs[0] = self.tokenizer.decode(self.tokenizer.encode(inputs[0])[-self.max_input_len:])

        return inputs,outputs,prefix

    def generate_reply(self, inputs,outputs,prefix):

        messages=[]
        for i in range(len(outputs)):
            messages.append({"role":"user", "content": inputs[i]})
            messages.append({"role":"assistant", "content": outputs[i]})


        messages.append({"role":"user", "content": inputs[-1]})



        tokens = self.tokenizer.apply_chat_template(messages)

        if not prefix is None and len(prefix)>0:
            prefix_tokens = self.tokenizer.encode(prefix)[1:]
            tokens = tokens+prefix_tokens

        input_ids = torch.LongTensor([tokens]).to(self.model.device)
        att_mask = torch.LongTensor([[1]*len(tokens)]).to(self.model.device)

        processed_args=self.process_generation_args(self.generation_args)

        outputs = self.model.generate(input_ids=input_ids,attention_mask=att_mask,**processed_args)
        responses=[]
        for i in range(outputs.shape[0]):
            text = self.tokenizer.decode(outputs[i].tolist()[len(tokens):])
            ind = text.find("</s>")
            if ind>0:
                text = text[:ind]
            responses.append(text)


        return responses, True



    
    def process_generation_args(self,generation_args):
        new_args=dict()
        if "batch_size" in generation_args.keys():

            new_args['num_return_sequences'] = generation_args["batch_size"]
        else:
            new_args['num_return_sequences'] == 1

        if "max_tokens" in generation_args.keys():
        
            new_args['max_new_tokens'] = generation_args["max_tokens"]
        else:
            new_args['max_new_tokens'] = 512

        if "temperature" in generation_args.keys():
            new_args['temperature'] = generation_args["temperature"]
            if new_args['temperature']>0:
                new_args["do_sample"]=True
            else:
                new_args["do_sample"]=False
        else:
            new_args["do_sample"]=True
            new_args['temperature'] =0
        if 'top_p' in generation_args.keys():
            new_args['top_p']=generation_args['top_p']

        if 'top_k' in generation_args.keys():
            new_args['top_k']=generation_args['top_k']
        else:
            new_args['top_k']=0





        return new_args




        
    def get_responses_conv(self,messages):

   

        if "temperature" in self.generation_args.keys():
            temperature = self.generation_args["temperature"]
        else:
            print("WARNING. Temperature not set, manually setting temperature")
            temperature=0.7

        input_args = self.process_generation_args(self.generation_args)


    

        for i in range(self.max_tries):

            try:


                response = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    **input_args
                )


                responses = [response.choices[i]['message']['content'] for i in range(input_args['n'])]
                

                if len(self.banned_phrases)>0 and i < (self.max_tries-1):
                    passed=False
                    for resp in responses:
                        passed_response=True
                        for phr in self.banned_phrases:
                            if phr.lower() in resp.lower():
                                passed_response=False

                        #we just need one response to pass
                        if passed_response:
                            passed=True
                    if not passed:
                        
                        print("Genetation iteration " +str(i) + " from Open AI didn't satisfy requirements, likely because it refused to follow instruction, regenerating with penalty.")
                        logit_bias=dict()
                        all_tokens = []
                        for resp in responses:
                            all_tokens+=self.tokenizer.encode(resp)

                        all_tokens = set(all_tokens)
                        for token in all_tokens:
                            logit_bias[str(token)]=-2


                        input_args['logit_bias']=logit_bias
                        

                        if temperature<0.4:
                            temperature=0.4
                        else:
                            temperature*=1.5
                        time.sleep(self.wait_per_try)

                
                        continue

                

                return responses,True
            except Exception as exception_str:
                print("Genetation iteration " +str(i) +" gave the following exception "+exception_str +"\n")
            
        print("Warning, open ai response generation error!!!!!!!!!!!!!!!!!!!!!!")
        return [self.error_response]*input_args['n'],False
    
    pass