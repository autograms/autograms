
import numpy as np



class Classifier():
    """
    Super class for classifier. Classifier is a language model that predicts multiple choice outputs from a restricted set of logits.

    Meant to be overriden by API calling class or class that uses local model.
    """

    def __init__(self):
        self.test_mode=False


    def __call__(self,content,answer_choices,sim_probs):


        if self.test_mode:
            #when in test mode, randomly sample classifier prediction according to proabilties
            pred_ind = np.random.choice(len(answer_choices),p=sim_probs)
            success=True
            return answer_choices[pred_ind],success
            
        else:
            #otherwise call classifier subclass to predict probabilities
            return self.predict_class(content,answer_choices)

    def set_test_mode(self,test_mode):
        self.test_mode=test_mode

    def predict_class(self,content,answer_choices):
        """
        args:
            content - string of text to be passed to classifier
            answer_choices - answer options, typically multiple choice (A,B,C etc.) or Yes/No 
        returns:
            prediction - class that was predicted
            success - whether model gave result without errors
        """
        raise NotImplementedError("predict_class() needs to be implemented by subclass classifier")


    def truncate_input(self,content):
        """
        args:
            content - string of text to be passed to classifier

        returns:
            trunctated_content - string that fits max input length set for model, or same string if under input length
        """
        raise NotImplementedError("truncate_input() needs to be implemented by subclass classifer")