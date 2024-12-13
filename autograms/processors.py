
import copy
import time
import random
import dill

from .memory import get_memory,set_memory

from .functional import parallel_wrapper

"""
Additional tools for wrapping autograms as well as parallel/batch processing. 
"""




class ReplyProcessor():

    def __init__(self,root_function,user_reply):
        self.root_function = root_function
        self.user_reply = user_reply

    def __call__(self,**kwargs):

        memory_object = get_memory()
        memory_object.add_user_reply(self.user_reply)

     

        result = self.root_function(**kwargs)
    
        return result.data['reply'], result.memory



class BatchProcessor:
    
    def __init__(self,root_function,batch_size):
        self.root_function = root_function
        self.batch_size = batch_size

    def __call__(self,**kwargs):

        args = [kwargs]*self.batch_size



        results = parallel_wrapper(self.root_function, args)
   
        return results
    









