

from .autogram_config import AutogramConfig

#from .nodes import  BaseNode
import ast

import json
from collections import OrderedDict
from .memory import MemoryObject, use_memory,set_memory,get_memory, clear_memory, SimpleMemory,SerializableMemory
from .program_control import AutogramsFunction
from . import apis
import dill, base64
import sys
import importlib


DEFAULT_API_KEYS={"load_from_env": True,"openai":"OPENAI_API_KEY"}


# from .graph_utils import get_graph, visualize_autogram
# from .autogram_utils import  process_node_id, post_process_user_responses, process_cell, simulate_interjections, get_interjection_states,python2df,df2python,get_exception_message
# from .statement_interpreter import StatementInterpreter
# from .models import CHATBOT_TYPES, CLASSIFIER_TYPES
# from .nodes import NODE_TYPES, EXPECTED_FIELDS
# from .special_functions import multiple_choice,yes_or_no,reply
# from .function import AutogramsFunction


from contextlib import contextmanager

import os






import time
import copy


    
def init_apis(api_keys):
    apis.api_keys = api_keys
    if 'openai' in api_keys:
        apis.openai_models.init_api(api_keys['openai'])



class Autogram():
    """
    A high-level interface for managing chatbot interactions using a Autograms.

    This class acts as a wrapper around the root AutogramsFunction, handling memory management,
    serialization, and interaction logic for chatbot responses.
    """
    def __init__(self,root_function=None,autogram_config=None,api_keys=None,global_reload_type="persistent_only",test_mode=False):
        """
        Initializes the Autogram object with a root function and configuration.

        Parameters:
        - root_function (AutogramsFunction): The root function defining the chatbot behavior.
        - autogram_config (AutogramConfig): Configuration object for the Autogram.
        - api_keys (dict): Dictionary of API keys, with an optional "load_from_env" to load keys from environment variables.
        - global_reload_type (string): "persistent_only" or "full". Persistent only will restore all globals defined with a "with persisent_globals()" scope. "full" will reload the parent module of root function every time with autogram.use_memory() is called 
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
                    new_api_keys[key] = os.environ[api_keys[key]]
                else:
                    new_api_keys[key]=api_keys[key]

        self.api_keys = new_api_keys
        self.test_mode=test_mode


        init_apis(new_api_keys)
       # set_prompt_config(self.config)

        self.circ_reference=False

        self.global_reload_type = global_reload_type


        if not root_function is None:

            self.root_function=root_function


            # if '_persistent_globals' in self.root_function.func.__globals_:
            #     self.persistent_globals_names = self.root_function.func.__globals__['_persistent_globals']
            #     self.persistent_globals_str = self.root_function.func.__globals__['_persistent_globals_str']

            self.root_module = sys.modules[self.root_function.func.__module__]


        else:
            self.root_function=None
            self.root_module=None

    @contextmanager
    def use_config(self):
        memory_object =SimpleMemory(config = self.config)
        set_memory(memory_object)

        memory_object.set_test_mode(self.test_mode)


        try:
            yield memory_object
        finally:
            clear_memory()

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

            set_memory(memory_object)


            try:
                yield memory_object
            finally:
               # if not self.root_function is None:

                
                memory_object.set_globals_snapshot()

                if self.global_reload_type=="full":
                    root_name= self.root_function.func.__name__
                    # self.root_function.func.__globals__.clear()
                    time0=time.time()
                    self.root_module = importlib.reload(self.root_module)
                    self.root_function = getattr(self.root_module,root_name)
                    print(f"reloaded module in {time.time()-time0} seconds")
                elif self.global_reload_type=="persistent_only":
          

                    if '_persistent_globals' in self.root_function.func.__globals__:
                        persistent_globals_names = self.root_function.func.__globals__['_persistent_globals']
                        persistent_globals_str = self.root_function.func.__globals__['_persistent_globals_str']

                        for key in persistent_globals_names:
                            if key in self.root_function.func.__globals__:
                                del self.root_function.func.__globals__[key]
                        persistent_globals_init = dill.loads(persistent_globals_str)
                        for key in persistent_globals_names:
                            self.root_function.func.__globals__[key]=persistent_globals_init[key]
                   
                else:
                    raise Exception("invalid global_reload type for autogram")




                                     
          
                clear_memory()
                

        else:
            
            set_memory(memory_object)

            try:
                yield memory_object
            finally:
                import sys
                import traceback
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_type is not None:
                    print("Exception occurred:")
                    traceback.print_exception(exc_type, exc_value, exc_traceback)
                
                clear_memory()


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

    def deserialize(self,data,serialization_type="partial"):

        """
        Deserializes memory from a given data string.

        Parameters:
        - data (str): Serialized memory data.
        - serialization_type (str): Type of serialization ("partial", "full", or "json").

        Returns:
        - MemoryObject: Deserialized memory object.
        """
        if serialization_type=="full":
            recovered_data= base64.b64decode(data)
            memory_object = dill.loads(recovered_data)
            self.config = memory_object.config
            self.root_function=memory_object.root_function
            return memory_object 

        else:

            if serialization_type=="partial":
                recovered_data= base64.b64decode(data)
                memory_dict = dill.loads(recovered_data)



              #  self.root_function.func.__globals__.update(persistent_globals)
                memory_object = MemoryObject(config = self.config,memory_dict = memory_dict,root_function= self.root_function)
                return memory_object 

        
            elif serialization_type=="json":
                raise NotImplementedError("json serialization not implemented yet, use partial for now")
                
                memory_dict  = jsonpickle.decode(data)
               # memory_dict = obj['memory']
                
                
                #persistent_globals = obj['non_func_globals']
               # self.root_function.func.__globals__.update(persistent_globals)
                memory_object = MemoryObject(config = self.config,memory_dict = memory_dict,root_function= self.root_function)
                return memory_object 

                
            else:
                raise Exception("invalid load type")
            
    def load(self,file_path,serialization_type="partial"):
        """
        Loads memory from a file.

        Parameters:
        - file_path (str): Path to the file containing serialized memory.
        - serialization_type (str): Type of serialization ("partial", "full", or "json").

        Returns:
        - MemoryObject: Loaded memory object.
        """
        if serialization_type=="full":
            with open(file_path,'rb') as fid:
                memory_object = dill.load(fid)
            self.config = memory_object.config
            self.root_function=memory_object.root_function
            return memory_object 

        else:

            if serialization_type=="partial":
                with open(file_path,'rb') as fid:
                     memory_dict = dill.load(fid)
                #memory_dict = obj['memory']
                
                #persistent_globals = obj['non_func_globals']
             #   self.root_function.func = dill.loads(self.func_original)
                #self.root_function.func.__globals__.update(persistent_globals)
                memory_object = MemoryObject(config = self.config,memory_dict = memory_dict,root_function= self.root_function)


        
            elif serialization_type=="json":
                raise NotImplementedError("json serialization not implemented yet, use partial for now")
                with open(file_path,'r') as fid:
                    data = fid.read()
                memory_dict = jsonpickle.decode(data)
                #memory_dict = obj['memory']
                
                # persistent_globals = obj['non_func_globals']
                # self.root_function.__globals__.func.update(persistent_globals)
                memory_object = MemoryObject(config = self.config,memory_dict = memory_dict,root_function= self.root_function)

                
                
            else:
                raise Exception("invalid load type")
            
        return memory_object
    def save(self,file,memory_object=None,serialization_type="partial"):
        """
        Saves the current memory state to a file.

        Parameters:
        - file (str): Path to the file where memory should be saved.
        - memory_object (MemoryObject, optional): Memory object to save. Defaults to current memory.
        - serialization_type (str): Type of serialization ("partial", "full", or "json").
        """
        if memory_object is None:
            memory_object = get_memory()

        memory_object.save(file,serialization_type)

    def serialize(self,memory_object=None,serialization_type="partial"):
        """
        Serializes the current memory state to a string.

        Parameters:
        - memory_object (MemoryObject, optional): Memory object to serialize. Defaults to current memory.
        - serialization_type (str): Type of serialization ("partial", "full", or "json").

        Returns:
        - str: Serialized memory data.
        """
        if memory_object is None:
            memory_object = get_memory()

        result = memory_object.serialize(serialization_type)
        return result
    

    #def init_new_memory(self,code_globals):

    
        

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

            memory_object = MemoryObject(config = self.config,memory_dict = memory_dict,root_function=self.root_function)
     


        memory_object.add_user_reply(user_reply)
        memory_object.set_test_mode(self.test_mode)
      #  memory_object.set_config(self.config)
        with self.use_memory(memory_object):
     

            result = self.root_function(**kwargs)
    
        return result.data['reply'], result.memory
    

    
    







    

        






