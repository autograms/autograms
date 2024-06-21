
from .classifier import Classifier
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class HuggingfaceClassifier(Classifier):
    def __init__(self,autogram_config,api_keys,chatbot=None):
        super().__init__()

        if chatbot is None or autogram_config.classifier_path!=autogram_config.chatbot_path:

            self.tokenizer = AutoTokenizer.from_pretrained(autogram_config.chatbot_path)
            self.model=AutoModelForCausalLM.from_pretrained(autogram_config.chatbot_path,torch_dtype=torch.float16)
            self.model.to("cuda:0")
        else:
            #share model objects with other bots
            self.tokenizer=chatbot.tokenizer
            self.model=chatbot.model

        self.max_tries = autogram_config.classifier_max_tries
        self.wait_per_try = autogram_config.classifier_wait_per_try
        self.model_name = autogram_config.classifier_path
        self.max_input_len = autogram_config.classifier_max_input_len
  
        self.test_mode = False


    def truncate_input(self,content):
        tokens = self.tokenizer.encode(content)
        if len(tokens)>self.max_input_len:
            new_tokens = tokens[-self.max_input_len:]
            content = self.tokenizer.decode(new_tokens)



        return content
    
    def predict_class(self,content,answer_choices):




        allowed_tokens =[]
        
        for answer in answer_choices:
            token=self.tokenizer.encode(answer)[1]
            allowed_tokens.append(token)
       
        
        tokens = self.tokenizer.apply_chat_template([{"role":"user", "content": content}])

        input_ids = torch.LongTensor([tokens]).to(self.model.device)

        
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids)
            logits = outputs[0][0,-1]

            class_pred_id = torch.argmax(logits[allowed_tokens]).item()
        
        return answer_choices[class_pred_id],True
