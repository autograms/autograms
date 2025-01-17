

from .autogram_config import AutogramConfig

import ast

import json
from collections import OrderedDict
from .memory import MemoryObject, use_memory,set_memory,get_memory, reset_memory, SimpleMemory,SerializableMemory
from .program_control import AutogramsFunction
from . import apis
import dill, base64
import sys
import importlib


DEFAULT_API_KEYS={"load_from_env": True,"openai":"OPENAI_API_KEY"}





from contextlib import contextmanager

import os



import time
import copy


    
def init_apis(api_keys,proxy_address=None,embedding_proxy_address=None):
    apis.api_keys = api_keys
    if api_keys is None:
        api_key = None
    else: 
        if 'openai' in api_keys:
            api_key = api_keys['openai']
        else:
            api_key = None

    apis.openai_models.init_api(api_key = api_key,proxy_address=proxy_address,embedding_proxy_address=embedding_proxy_address)
    
def load_autogram(filepath):
    import importlib.util, sys

    spec = importlib.util.spec_from_file_location("autogram_module", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # **Manually** register in sys.modules
    sys.modules["autogram_module"] = module

    chatbot_func = getattr(module, "chatbot", None)
    init_func = getattr(module, "init_chatbot", None)

    return chatbot_func, init_func


# def load_autogram(filepath):
#     spec = importlib.util.spec_from_file_location("autogram_module", filepath)
#     module = importlib.util.module_from_spec(spec)
#     spec.loader.exec_module(module)

#     # Optionally: module.init_chatbot() or something
#     chatbot_func = getattr(module, "chatbot", None)
#     init_func = getattr(module, "init_chatbot", None)

#     return chatbot_func, init_func

@contextmanager
def use_config(config,test_mode=False):
    """
    A simple way to set the config 
    """
    memory_object =SimpleMemory(config = config)
    token= set_memory(memory_object)

    memory_object.set_test_mode(test_mode=test_mode)


    try:
        yield memory_object
    finally:
        reset_memory(token)

class Autogram():
    """
    A high-level interface for managing chatbot interactions using a Autograms.

    This class acts as a wrapper around the root AutogramsFunction, handling memory management,
    serialization, and interaction logic for chatbot responses.
    """
    def __init__(self,root_function=None,autogram_config=None,api_keys=None,test_mode=False):
        """
        Initializes the Autogram object with a root function and configuration.

        Parameters:
        - root_function (AutogramsFunction): The root function defining the chatbot behavior.
        - autogram_config (AutogramConfig): Configuration object for the Autogram.
        - api_keys (dict): Dictionary of API keys, with an optional "load_from_env" to load keys from environment variables.
        - test_mode (boolean): uses automated model outputs for every turn, good for finding bugs in the program without needing to call apis
        """
        if autogram_config is None:
            autogram_config = AutogramConfig()

        self.config = autogram_config
        if api_keys is None:
            api_keys=DEFAULT_API_KEYS
        new_api_keys={}
        if "load_from_env" in api_keys:
            load_from_env=api_keys["load_from_env"]
        else:
            load_from_env=False

        for key in api_keys:
            if not(key=="load_from_env"):
                if load_from_env:
                    if api_keys[key] in os.environ:
                    
                        new_api_keys[key] = os.environ[api_keys[key]]
                    else:
                        new_api_keys=None
                        
                else:
                    new_api_keys[key]=api_keys[key]

        self.api_keys = new_api_keys
        self.test_mode=test_mode



        if self.config.chatbot_type == 'openai':

            init_apis(new_api_keys)
        else:
            init_apis(new_api_keys,proxy_address = self.config.proxy_address,embedding_proxy_address=self.config.embedding_proxy_address)
            

        self.circ_reference=False



        if not root_function is None:


            self.root_function=root_function


            self.root_module = sys.modules[self.root_function.func.__module__]




        else:
            raise Exception("must define root_function")
            self.root_function=None
            self.root_module=None



    @contextmanager
    def use_config(self):
        memory_object =SimpleMemory(config = self.config)
        token=set_memory(memory_object)

        memory_object.set_test_mode(self.test_mode)


        try:
            yield memory_object
        finally:
            reset_memory(token)

    @contextmanager
    def use_memory(self,memory_object=None,memory_dict=None):
        """
        Sets and manages memory for chatbot sessions or replies, ensuring proper cleanup.

        Parameters:
        - memory_object (MemoryObject, SerializableMemory, or SimpleMemory): The memory object to use.
        - memory_dict (dict): Dictionary containing serialized memory state.

        Yields:
        - memory_object: The active memory object for the session.
        """
    
        if memory_object is None:
            

            if not(self.root_function is None):

                memory_object = MemoryObject(config = self.config,memory_dict = memory_dict,root_function=self.root_function)
            else:
                
                memory_object = SimpleMemory(config = self.config,memory_dict = memory_dict)

      
        
        memory_object.set_test_mode(self.test_mode)
        if isinstance(memory_object,SerializableMemory):
            
         #   import pdb;pdb.set_trace()
            self.root_function.func.__globals__.update(memory_object.memory_dict["globals_snapshot"])

            token = set_memory(memory_object)


            try:
                yield memory_object
            finally:
     
                
                memory_object.set_globals_snapshot()


                if '_persistent_globals' in self.root_function.func.__globals__:
                    persistent_globals_names = self.root_function.func.__globals__['_persistent_globals']
                    persistent_globals_str = self.root_function.func.__globals__['_persistent_globals_str']

                    for key in persistent_globals_names:
                        if key in self.root_function.func.__globals__:
                            del self.root_function.func.__globals__[key]
                    persistent_globals_init = dill.loads(persistent_globals_str)
                    for key in persistent_globals_names:
                        self.root_function.func.__globals__[key]=persistent_globals_init[key]
                   

                                     
                reset_memory(token)
                

        else:
            
            token = set_memory(memory_object)

            try:
                yield memory_object
            finally:
                import sys
                import traceback
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_type is not None:
                    print("Exception occurred:")
                    traceback.print_exception(exc_type, exc_value, exc_traceback)
                
                reset_memory(token)


    def add_user_reply(self,user_reply=None):
        """
        Adds a user reply to the current memory.

        Parameters:
        - user_reply (str): The user's reply to be added to memory.

        Raises:
        - Exception: If no memory is set.
        """
        memory_object = get_memory()

        if memory_object is None:
            raise Exception("memory must be set to add user reply")
        memory_object.add_user_reply(user_reply)

    def deserialize(self,data):

        """
        Deserializes memory from a given data string.

        Parameters:
        - data (str): Serialized memory data.

        Returns:
        - MemoryObject: Deserialized memory object.
        """
        recovered_data= base64.b64decode(data)
        memory_dict = dill.loads(recovered_data)



        #  self.root_function.func.__globals__.update(persistent_globals)
        memory_object = MemoryObject(config = self.config,memory_dict = memory_dict,root_function= self.root_function)
        return memory_object 
            
    def load(self,file_path):
        """
        Loads memory from a file.

        Parameters:
        - file_path (str): Path to the file containing serialized memory.

        Returns:
        - MemoryObject: Loaded memory object.
        """
        with open(file_path,'rb') as fid:
                memory_dict = dill.load(fid)
        #memory_dict = obj['memory']
        
        #persistent_globals = obj['non_func_globals']
        #   self.root_function.func = dill.loads(self.func_original)
        #self.root_function.func.__globals__.update(persistent_globals)
        memory_object = MemoryObject(config = self.config,memory_dict = memory_dict,root_function= self.root_function)

            
        return memory_object
    def save(self,file,memory_object=None):
        """
        Saves the current memory state to a file.

        Parameters:
        - file (str): Path to the file where memory should be saved.
        - memory_object (MemoryObject, optional): Memory object to save. Defaults to current memory.

        """
        if memory_object is None:
            memory_object = get_memory()

        memory_object.save(file)

    def serialize(self,memory_object=None):
        """
        Serializes the current memory state to a string.

        Parameters:
        - memory_object (MemoryObject, optional): Memory object to serialize. Defaults to current memory.

        Returns:
        - str: Serialized memory data.
        """
        if memory_object is None:
            memory_object = get_memory()

        result = memory_object.serialize()
        return result
    

    #def init_new_memory(self,code_globals):

    
    def init_memory(self,memory_dict=None):
        return MemoryObject(config = self.config,memory_dict = memory_dict,root_function=self.root_function)

    def reply(self,user_reply="",memory_object=None,memory_dict=None,**kwargs):
        """
        Generates a chatbot reply based on user input and memory.

        Parameters:
        - user_reply (str): The user's input message.
        - memory_object (MemoryObject, optional): Memory object to use for the reply.
        - memory_dict (dict, optional): dictionary memory to initialize a new memory object.
        - test_mode (bool): If True, enables test mode for the memory object, which gives fast automatic replies without calling apis.
        - **kwargs: Additional arguments passed to the root function.

        Returns:
        - tuple: A reply message and the updated memory object.
        """
        old_memory_object = get_memory()
        if not(old_memory_object is None) and (not(memory_dict is None) or not(memory_object is None)):
   
            print("Warning, Autogram.reply() method called with memory argument when existing cached memory found. This will overwrite and then reset the cached memory.")
                                            

        if memory_object is None:
            memory_object = self.init_memory(memory_dict)


        memory_object.add_user_reply(user_reply)
        memory_object.set_test_mode(self.test_mode)

        with self.use_memory(memory_object):
     

            result = self.root_function(**kwargs)
    
        return result.data['reply'], result.memory
    

    
    

    def apply(self,user_reply=None,memory_object=None,memory_dict=None,func=None,**kwargs):
        """
        Generates a chatbot output based on user input and memory.

        Parameters:
        - user_reply (str): The user's input message.
        - memory_object (MemoryObject, optional): Memory object to use for the reply.
        - memory_dict (dict, optional): dictionary memory to initialize a new memory object.
        - test_mode (bool): If True, enables test mode for the memory object, which gives fast automatic replies without calling apis.
        - **kwargs: Additional arguments passed to the root function.

        Returns:
        - tuple: A reply message and the updated memory object.
        """
        old_memory_object = get_memory()
        if not(old_memory_object is None) and (not(memory_dict is None) or not(memory_object is None)):
   
            print("Warning, Autogram.reply() method called with memory argument when existing cached memory found. This will overwrite and then reset the cached memory.")
                                            

        if memory_object is None:
            memory_object = self.init_memory(memory_dict)

        if not user_reply is None:
            memory_object.add_user_reply(user_reply)
        memory_object.set_test_mode(self.test_mode)
      #  memory_object.set_config(self.config)
        if func is None:


            with self.use_memory(memory_object):
        

                result = func(**kwargs)
        else:
            with self.use_memory(memory_object):
                result =  func(**kwargs)
        
        return result





    

        






