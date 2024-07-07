from .classifier import Classifier
import openai 
import tiktoken
import time
import pkg_resources


openai_version = pkg_resources.get_distribution("openai").version

legacy_openai= [int(x) for x in openai_version.split('.')][0]==0



class OpenAIClassifier(Classifier):
    def __init__(self,autogram_config,api_keys,chatbot=None):
        super().__init__()
        self.max_tries = autogram_config.classifier_max_tries
        self.wait_per_try = autogram_config.classifier_wait_per_try
        self.model_name = autogram_config.classifier_path   
        if "openai" in api_keys.keys():
            if legacy_openai:
                self.client = openai
                self.client.api_key = api_keys["openai"]
            else:
                from openai import OpenAI
                self.client =  OpenAI(api_key=api_keys["openai"])
        else:
            raise Exception("missing Open AI API key")     
        self.test_mode = False
        self.max_input_len = autogram_config.classifier_max_input_len
        self.tokenizer = tiktoken.encoding_for_model(self.model_name)

    def truncate_input(self,content):
        tokens = self.tokenizer.encode(content)
        if len(tokens)>self.max_input_len:
            new_tokens = tokens[-self.max_input_len:]
            content = self.tokenizer.decode(new_tokens)



        return content


    def predict_class(self,content,answer_choices):


        messages = [{"role":"user", "content": content}]

        answer_dict=dict()

        """
        logit biases are used to prevent model from generated token outside of the answer choices
        """
        for answer in answer_choices:
            token=self.tokenizer.encode(answer)
            answer_dict[str(token[0])]=100

        for i in range(self.max_tries):

       
            
            try:
                if legacy_openai:
                    response = self.client.ChatCompletion.create(model=self.model_name,logit_bias=answer_dict,messages=messages,temperature=0.0,max_tokens=1,n=1)
                    return response.choices[0]["message"]["content"],True
                else:
                    response = self.client.chat.completions.create(model=self.model_name,logit_bias=answer_dict,messages=messages,temperature=0.0,max_tokens=1,n=1)
        
                    return response.choices[0].message.content,True
           
            except Exception as exception_str:


                print("open ai classifier failed, retrying. Error message was: "+str(exception_str))
    
                
                time.sleep(self.wait_per_try)

        print("Warning, open ai state classifier error!!!!!!!!!!!!!!!!!!!!!!")
        
        return "Failed",False