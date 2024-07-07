import openai
import time
import tiktoken
import numpy as np
from .chatbot import Chatbot
import pkg_resources


openai_version = pkg_resources.get_distribution("openai").version

legacy_openai= [int(x) for x in openai_version.split('.')][0]==0


class OpenAIChatbot(Chatbot):

    def __init__(self,autogram_config,api_keys,chatbot=None):

        super().__init__(autogram_config)


        if "openai" in api_keys.keys():
            if legacy_openai:
                self.client = openai
                self.client.api_key = api_keys["openai"]
            else:
                from openai import OpenAI
                self.client =  OpenAI(api_key=api_keys["openai"])
        else:
            raise Exception("missing Open AI API key") 
        


        self.generation_args=autogram_config.chatbot_generation_args
        self.max_input_len = autogram_config.chatbot_max_input_len
        self.model_name=autogram_config.chatbot_path
        self.max_tries=autogram_config.chatbot_max_tries
        self.wait_per_try=autogram_config.chatbot_wait_per_try
        self.banned_phrases=autogram_config.banned_phrases
        self.error_response= autogram_config.error_response


        self.test_mode = False
        self.tokenizer = tiktoken.encoding_for_model(self.model_name)
        

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


    def generate_reply(self, inputs,outputs,prefix=None):

        messages=[]
        for i in range(len(outputs)):
            messages.append({"role":"user", "content": inputs[i]})
            messages.append({"role":"assistant", "content": outputs[i]})

        messages.append({"role":"user", "content": inputs[-1]})


        if self.test_mode:
            if ['batch_size'] in self.generation_args:
                texts = ["<test mode enabled, no response available.>"]*self.generation_args['batch_size']
            else:
                texts = ["<test mode enabled, no response available.>"]

            success=True


        else:
        
            texts,success = self.get_responses_conv(messages)


        return texts,success
    
    def process_generation_args(self,generation_args):
        new_args=dict()
        if "batch_size" in generation_args.keys():

            new_args['n'] = generation_args["batch_size"]
        else:
            new_args['n'] = 1

        if "max_tokens" in generation_args.keys():
        
            new_args['max_tokens'] = generation_args["max_tokens"]
        else:
            new_args['max_tokens'] = 512


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
            

                if legacy_openai:
                    response = self.client.ChatCompletion.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=temperature,
                        **input_args
                    )
                
                    responses = [response.choices[i]['message']['content'] for i in range(input_args['n'])]


                else:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=temperature,
                        **input_args
                    )
                


                    responses = [response.choices[i].message.content for i in range(input_args['n'])]
                

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
                        """
                        Handling of banned phrases. If response generated banned phrases, we use the logit bias to downweight the whole respond.
                        Usually banned phrases are when model refuses to reply (ex: I'm sorry, I can't do that.)
                        This most commonly happens when it is ignoring an instruction we are giving it, common when simulating the user.
                        """
                        
                        print("Generation iteration " +str(i) + " from Open AI didn't satisfy requirements, likely because it refused to follow instruction, regenerating with penalty.")
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
                print("Genetation iteration " +str(i) +" gave the following exception "+str(exception_str) +"\n")
            
        print("Warning, open ai response generation error!!!!!!!!!!!!!!!!!!!!!!")
        return [self.error_response]*input_args['n'],False
    



