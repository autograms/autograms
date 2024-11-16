

from .autogram_config import AutogramConfig

#from .nodes import  BaseNode
import ast

import json
from collections import OrderedDict
from .memory import MemoryObject, use_memory,set_memory,get_memory, clear_memory, SimpleMemory,SerializableMemory
from .program_control import AutogramsFunction
from . import apis
import dill, base64


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


# @context_manager
# def use_autogram(memory_object=None,memory_dict=None,autogram_config=None,api_keys={},root_function=None,test_mode=False):
#     if autogram_config is None:
#         autogram_config = AutogramConfig()
#     config = autogram_config
#     new_api_keys={}
#     if "load_from_env" in api_keys:
#         load_from_env=api_keys["load_from_env"]
#     else:
#         load_from_env=False

#     for key in api_keys:
#         if not(key=="load_from_env"):
#             if load_from_env:
#                 new_api_keys[key] = os.environ[api_keys[key]]
#             else:
#                 new_api_keys[key]=api_keys[key]

#     init_apis(api_keys)
    

#     if not root_function is None:
#         all_functions = {} #root_function.get_all_functions()
#         for key in all_functions.keys():
#             all_functions[key].update_config(autogram_config)

#         function_cache = all_functions


#     else:
    
#         function_cache=None
#     if memory_object is None:
#         memory_object = MemoryObject(config = config,memory_dict = memory_dict,function_cache=function_cache)
#     memory_object.set_test_mode(test_mode)

#     set_memory(memory_object)

#     try:
#         yield memory_object
#     finally:
#         clear_memory()

    
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
    def __init__(self,root_function=None,autogram_config=None,api_keys=None,enable_circular_reference=False):
        """
        Initializes the Autogram object with a root function and configuration.

        Parameters:
        - root_function (AutogramsFunction): The root function defining the chatbot behavior.
        - autogram_config (AutogramConfig): Configuration object for the Autogram.
        - api_keys (dict): Dictionary of API keys, with an optional "load_from_env" to load keys from environment variables.
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


        init_apis(new_api_keys)
       # set_prompt_config(self.config)

        self.circ_reference=False


        if not root_function is None:

            self.root_function=root_function

            self.globals_original= dill.dumps(self.root_function.func.__globals__.copy())


        
            if b'__main__' in self.globals_original or len(self.globals_original) < 100:
                if enable_circular_reference:
                    if b'__main__' in self.globals_original:
                        print("WARNING: circular reference to autogram detected due to @autograms_function being defined in main file--but will proceed since `enable_circular_reference` set to True. Enabling this prevents the autogram from having multiple independent memories, and could lead to other unexpected behavior. Production use cases should have @autograms_function in separate file from main and import the root function.")
                    else:
                         print("WARNING: possible circular reference to autogram detected. Will proceed since enable_circular_reference set to True. This is generally not recommeneded for anything except test usecases, and also prevents the autogram from having multiple independent memories. To prevent circular reference, make sure any @autograms_function decorated function does not have visibility of the Autogram object.")
                    self.circ_reference=True

                else:
                    
                    if b'__main__' in self.globals_original:
                        raise Exception("circular reference detected due to autograms_function being declared in main file, which also references the Autogram. To override this error and use a workaround, set enable_circular_reference=True when initializing the autogram.")
                    else:
                        print("WARNING: Possible circular reference to autogram detected, which will likely lead to an error due to globals in your calling scope being erased. It is recommended to avoid putting @autograms_function in the __main__ file, and that @autograms_function does not have visibility of the Autogram object. If you would like a workaround to enable these behaviors anyway, you can initialize your Autogram object with `enable_circular_reference=True`, however this workaround is only suitable for testing purposes and may sometimes lead to unexpected behavior.")


            self.enable_circular_reference=enable_circular_reference
            if self.enable_circular_reference:

                print("Warning: enable_circular_reference set to True and circular references will be allowed, allowing @autograms_function to be used directly in the __main__ file. It is strongly recommended to disable this for anything other than testing purposes as this causes the chatbot and program calling the chatbot to have shared global variables, which may lead to unexpected edge cases. It is also not suitable for applications where an autogram needs to have multiple independent memory instances (talking to multiple users for instance), because it prevents the chatbots memory from being fully reset after calls to autogram.reply().\n")


            #self.globals_original= dill.dumps(root_function.func.__globals__.copy())

            # for function_name in self.function_cache:
            #     func = self.function_cache[function_name]
            #     graph = func.check_graph(other_functions=self.function_cache)
        else:
            self.root_function=None

    @contextmanager
    def use_config(self):
        memory_object =SimpleMemory(config = self.config)
        set_memory(memory_object)


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

            if self.root_function is None:

                memory_object = MemoryObject(config = self.config,memory_dict = memory_dict,root_function=self.root_function)
            else:
                
                memory_object = SimpleMemory(config = self.config,memory_dict = memory_dict)

        

        if isinstance(MemoryObject ,SerializableMemory):
            self.root_function.func.__globals__.update(memory_object.memory_dict["globals_snapshot"])

            set_memory(memory_object)


            try:
                yield memory_object
            finally:
                if not self.root_function is None:

                 
                    memory_object.set_globals_snapshot()
                    
                    
                   
                    if not self.circ_reference:
                        self.root_function.func.__globals__.clear()


                        globals_dict = dill.loads(self.globals_original)
                        # if len(globals_original)==0:
                        #     print("Error caching global variables. This can happen if the autogram is used in the same file as an @autograms_function that it calls. The interpreter becomes a global variable in it's own program, which is unstable. Define these in separate files to prevent errors.")
                

                        self.root_function.func.__globals__.update(globals_dict)
          
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

    
        

    def reply(self,user_reply="",memory_object=None,memory_dict=None,test_mode=False,**kwargs):
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
        memory_object.set_test_mode(test_mode)
      #  memory_object.set_config(self.config)
        with self.use_memory(memory_object):
     

            result = self.root_function(**kwargs)
    
        return result.data['reply'], result.memory
    

    
    







    

# class Autogram():

#     """
#     Autogram is the class that executes a program defined by a set of nodes and their associated attributes
#     It holds autogram.nodes, which is a dictionary of all the nodes that have been loaded.
#     It contains functions to reply to the user, simulate the user's reply, or call any callable AutoGRAMS module as a function
#     """
   
#     def __init__(self,autogram_config=None,api_keys={},allow_incomplete=None,root_function=None):

#         """
#         Initializes autogram object
#         Args:
#             autogram_config - object of type AutogramConfig that defines all the autogram settings, default prompts, and prompt tempalaes
#             df - DataFrame object that results from loading the spreadsheet. if df is included, nodes will be defined when autogram is initialized.
#             api_keys - dictionary where keys are model type (ex: 'openai') and values are api keys
#             allow_incomplete - boolean, allows an autogram to be defined without valid api keys or fully connected nodes
#         """

#         if allow_incomplete is None:

#             allow_incomplete=False


#         if autogram_config is None:
#             autogram_config = AutogramConfig()
        
#         if autogram_config.self_referential:
#             #nodes with python_function can access and modify the autogram, requires coding autogram with care
#             autogram_config.python_modules["self"]=self


#         autogram_config.python_modules["reply"]=reply
#         autogram_config.python_modules["yes_or_no"]=yes_or_no
#         autogram_config.python_modules["multiple_choice"]=multiple_choice


        
            
#         self.config = autogram_config

         
#         new_api_keys={}
#         if "load_from_env" in api_keys:
#             load_from_env=api_keys["load_from_env"]
#         else:
#             load_from_env=False

#         for key in api_keys:
#             if not(key=="load_from_env"):
#                 if load_from_env:
#                     new_api_keys[key] = os.environ[api_keys[key]]
#                 else:
#                     new_api_keys[key]=api_keys[key]

#         self.api_keys = new_api_keys
#         self.allow_incomplete=allow_incomplete
#         self.statement_interpreter = StatementInterpreter(autogram_config,self.api_keys)


#         if allow_incomplete:

#             try:
#             #dictionaries CHATBOT_TYPES and CLASSIFIER_TYPES store the allowable chatbots and classifier classes
#                 self.chatbot = CHATBOT_TYPES[autogram_config.chatbot_type](autogram_config,self.api_keys)
#                 self.classifier = CLASSIFIER_TYPES[autogram_config.classifier_type](autogram_config,self.api_keys,chatbot=self.chatbot)
#                 self.user_bot = CHATBOT_TYPES[autogram_config.chatbot_type](autogram_config,self.api_keys,chatbot=self.chatbot)
#             except:
#                 self.chatbot =None
#                 self.classifier=None
#                 self.user_bot =None
#                 print("Warning, some model API keys are missing. This autogram will give errors if models are called.")


#         else:
#             #dictionaries CHATBOT_TYPES and CLASSIFIER_TYPES store the allowable chatbots and classifier classes
#             self.chatbot = CHATBOT_TYPES[autogram_config.chatbot_type](autogram_config,self.api_keys)
#             self.classifier = CLASSIFIER_TYPES[autogram_config.classifier_type](autogram_config,self.api_keys,chatbot=self.chatbot)
#             self.user_bot = CHATBOT_TYPES[autogram_config.chatbot_type](autogram_config,self.api_keys,chatbot=self.chatbot)

#         #NODE_TYPES is a dictionary where the keys are the allowable action names and values are the corresponding node classes
#         self.node_types=NODE_TYPES

#         #EXPECTED_FIELDS is a list of all allowable fields
#         self.expected_fields=EXPECTED_FIELDS

#         #default initial state ofr autogram, set to "start1" if not changed
#         self.start_state=autogram_config.start_state

        
#         self.test_mode=False
  
#         self.nodes= OrderedDict()
#         self.node_args=list()


#         if not root_function is None:
#             all_functions = root_function.get_all_functions()
#             for key in all_functions.keys():
#                 all_functions[key].update_config(self.config)

#             self.function_cache = all_functions
#             self.root_function=root_function


#             for function_name in self.function_cache:
#                 func = self.function_cache[function_name]
#                 graph = func.check_graph(other_functions=self.function_cache)

    

            


#         # if not df is None:
#         #     #loads nodes into autogram from data frame
#         #     self.add_nodes_from_data_frame(df)

#         #     #tests added nodes and update neccesary variables
#         #     self.update()




#     def init_memory(self,memory_dict=None):

#         memory = MemoryObject(memory_dict = memory_dict,root_function = self.root_function,autogram_config=self.config, interpreter = self.statement_interpreter,function_cache=self.function_cache)
#         return memory
    

#     def visualize(self,root_path,graph_format="png"):

#         for function_name in self.function_cache:
#             func = self.function_cache[function_name]
#             graph = func.check_graph()

#             visualize_autogram(func,graph,root_path=root_path,graph_format=graph_format)






#     def update(self,include_inst=False,finalize=True):

#         """
#         Call update once all nodes have been loaded. If finalize is True or allow incomplete is False, it tests the graph for errors. It also updates the interjection nodes, which are nodes that can be reached from any chat state.
#         """

#         if finalize==True:
#             self.allow_incomplete=False
        

#         #test_transitions(self.nodes)
#         graph = get_graph(self.nodes,allow_undefined=self.allow_incomplete,include_inst=include_inst)
#         self.graph=graph
        

        
#        # self.inter_nodes = get_interjection_states(self.nodes)


#     def update_api_keys(self,api_keys):

#         new_api_keys={}
#         if "load_from_env" in api_keys:
#             load_from_env=api_keys["load_from_env"]
#         else:
#             load_from_env=False

#         for key in api_keys:
#             if not(key=="load_from_env"):
#                 if load_from_env:
#                     new_api_keys[key] = os.environ[api_keys[key]]
#                 else:
#                     new_api_keys[key]=api_keys[key]

#         self.api_keys = new_api_keys
#         self.statement_interpreter = StatementInterpreter(self.config,self.api_keys)

#         if self.chatbot is None:
#             self.chatbot = CHATBOT_TYPES[self.config.chatbot_type](self.config,self.api_keys)
#             self.classifier = CLASSIFIER_TYPES[self.config.classifier_type](self.config,self.api_keys,chatbot=self.chatbot)
#             self.user_bot = CHATBOT_TYPES[self.config.chatbot_type](self.config,self.api_keys,chatbot=self.chatbot)






#     def reply(self,user_reply="",memory_object=None,memory_dict=None,test_mode=False):
#         """
#         Function to reply when a new user response is received. This function will apply nodes and transitions until it reaches a node that allows a reply (usually a chat type node)
#         Args:
#             user_reply - string that gives last user reply
#             memory_object - MemoryObject that keeps track of memory of conversation history, states, and variables. Will define memory_object from memory_dict if memory_object isn't defined
#             memory_dict - json like dictionary that defines memory object. If both memory_object and memory_dict are undefined, will initialize new memory_object.
#             set_state - string that gives starting state, can be used to override the last state stored in the memory object. Not needed otherwise.
#             test_mode - running in test modes mean that all models and APIs will give a default response. Useful for quickly testing random trajectories through graph
#             return_as_dict - if False, returns MemoryObject, otherwise returns dictionary that defines memory object
#         Returns:
#             response - string that gives model's response to user_reply
#             memory_object (or memory_dict if return_as_dict is set) - MemoryObject that keeps track of conversation history, states, and variables
#         """
 
    


#         self.test_mode = test_mode
#         self.chatbot.set_test_mode(test_mode)
#         self.classifier.set_test_mode(test_mode)

#         if memory_object is None:

#             memory_object = self.init_memory(memory_dict=memory_dict)

#         memory_object.add_user_reply(user_reply)




#         try:
#            result = self.root_function()

#         except ReplyExit as reply_exc:
#             return reply_exc['reply'],memory_object,None
        


#         return result,memory_object,None
                
            

            



        

    # def add_nodes_from_data_frame(self,df,reset=False):
    #     """
    #     Function to add nodes from a dataframe
    #     Args:
    #         df - dataframe from spreadsheet
    #         reset - use to overwrite nodes (instead of add to currently saved nodes)
    #     """

    #     if reset:
    #         self.nodes=OrderedDict()

    #     if "Name" in df.keys():
    #         names = df["Name"]
    #     elif "name" in df.keys():
    #         names = df["name"]
            
    #     else:
    #         raise Exception("Error: must have `name` in data frame. `Name` field may be missing from csv.")

        
    #     if "Function" in df.keys():
    #         functions = df["Function"]

    #     elif "Function" in df.keys():
    #         functions = df["function"]
    #     else:
    #         functions = ["main"]*len(names)


    #     for i in range(len(functions)):
    #         if functions[i]=="":
    #             functions[i]="main"

    #     if "main" in functions:
    #         root_function_name="main"
    #     else:
    #         root_function_name=functions[0]

        


    #     for field in df.keys():

    #         field_name = field.lower().replace(" ","_")
    #         if not field_name in self.expected_fields:
    #             if field[-1]==' ':
    #                 raise Exception("Field "+str(field)+ " has a trailing space, please delete the trailing space and try again." )
    #             else:
    #                 raise Exception("Invalid field "+str(field)+".")
        

    #     function_set = set(functions)
    #     function_dict=dict()

    #     all_functions=dict()



    #     for i in range(len(names)):
    #         if functions[i] in function_set:
    #             function_dict[functions[i]]["indexes"].append(i)

    #             if df[field][i]["action"]=="function_def":

    #                 if "def" in function_dict[functions[i]].keys():
    #                     raise Exception("multiple function definitions for function: "+functions[i])
    #                 else:
    #                     function_dict[functions[i]]["def"]=i
    #                     function_dict[functions[i]]["found"]=True



    #         else:
                
    #             function_dict[functions[i]] = {"indexes":[i],"found":False}
    #             if "def" in function_dict[functions[i]].keys():
    #                 raise Exception("multiple function definitions for function: "+functions[i])
    #             else:
    #                 function_dict[functions[i]]["def"]=i
    #                 function_dict[functions[i]]["found"]=True

    #     for func_name in function_dict.keys():
    #         if function_dict[func_name]["found"]==False and len(function_dict.keys())>1:
    #             raise Exception ("function : "+func_name + " is missing a definition node")

    

    #         other_node_args=[]
    #         def_id=-1
    #         if function_dict[func_name]["found"]:
    #             def_id =function_dict[func_name]["def"]
    #             def_node_arg =self.extract_node_fields_from_df(df,def_id)

                
                
    #         else:
    #             first_node = function_dict[func_name]["indexes"][0]
    #             def_node_arg ={"action":"function_def","name":"_def_"+func_name,"instruction":"function()","transitions":[names[first_node]]}

    #         if "indexes" in function_dict[func_name]:
    #             indexes = function_dict[func_name]["indexes"]
    #             for i in indexes:
    #                 if not i==def_id:
    #                     other_node_args.append(self.extract_node_fields_from_df(df,i))


    #         function = AutogramsFunction(def_node=def_node_arg,body_nodes=other_node_args)

    #         all_functions[func_name]=function

        

    #     for func_name in all_functions.keys():
            
    #         all_functions[func_name].add_to_globals(all_functions)

    #     root_function = all_functions[root_function_name]

        
    #    self.init_default_memory(root_function)




























# ########################################## below may be deprecated, need to check


#     def extract_node_fields_from_df(self,df,index):
#         node_fields=dict(zip(self.expected_fields, [None]*len(self.expected_fields)))
#         for field in df.keys():
#             field_name = field.lower().replace(" ","_")
#             node_fields[field_name] = process_cell(df[field][index])

#         python_node_fields = df2python(**node_fields)

#         return python_node_fields




#     def add_node_plus(self,**kwargs):
#         name_orig = kwargs['name']

#         if "lineno" in kwargs:
#             lineno =  kwargs["lineno"]
#         else:
#             lineno=None
        
#         if "preprocess_functions" in kwargs:

#             if "(" in kwargs['name']:
#                 self.add_node(**kwargs)
#                 last_node = list(self.nodes.keys())[-1]
#                 raise Exception("callable node " + str(self.nodes[last_node]) + " cannot have preprocess functions")
        
#             preprocess_functions = 1*kwargs["preprocess_functions"]
            
#             names = [name_orig]+[name_orig+"_step_"+str(i)+"_" for i in range(len(preprocess_functions))]
        
#             for i in range(len(preprocess_functions)):

#                 self.add_node(name=names[i], transitions = [names[i+1]],action="global_function",instruction=preprocess_functions[i],lineno=lineno)
            
#             kwargs['name'] =  names[-1]
#             del kwargs["preprocess_functions"]
        

        

#         if "postprocess_functions" in kwargs:
#             if "(" in kwargs['name']:
#                 self.add_node(**kwargs)
#                 last_node = list(self.nodes.keys())[-1]
#                 raise Exception("callable node " + str(self.nodes[last_node]) + " cannot have postprocess functions")
          
#             postprocess_functions = 1*kwargs["postprocess_functions"]
#             names = [name_orig+"_post_step_"+str(i)+"_" for i in range(len(postprocess_functions))]

#             transition_args = ["transitions","transition_question","transition_choices"]
#             orig_transition = dict()
#             for arg in transition_args:
#                 if arg in kwargs.keys():
#                     orig_transition[arg] = 1*kwargs[arg]
#                     del kwargs[arg]

#             del kwargs["postprocess_functions"]
#             kwargs["transitions"]=[names[0]]


#             self.add_node(**kwargs)

#             for i in range(len(postprocess_functions)-1):
                
#                 self.add_node(name = names[i],transitions = [names[i+1]],action="global_function",instruction = postprocess_functions[i],lineno=lineno)
    
#             self.add_node(name = names[-1],action="global_function",instruction = postprocess_functions[-1],**orig_transition,lineno=lineno)

        


#         else:

#             self.add_node(**kwargs)
     

                
                
#     def add_node(self,**kwargs):
#         """
#         Function to add a single node
#         Args:
#             **kwargs -- args used to initialize a node. See __init__() function for nodes in BaseNode class.
#         """
#         if "action" in kwargs:
#             self.node_args.append(copy.deepcopy(kwargs))
    
#             node_class = self.node_types[kwargs['action']]

            

#             if "name" in kwargs:
#                 node = node_class(autogram_config=self.config,statement_interpreter=self.statement_interpreter,**kwargs)
     
#                 if node.name in self.nodes.keys():
#                     raise Exception("Duplicate node name "+str(kwargs['name']))
                

#                 else:

#                     self.nodes[node.name] = node
#             else:
#                 raise Exception("Error: Node missing a name. Each new node needs a name")


#         else:
#             raise Exception("Error: Node missing an action. Each new node needs an action")


#     def convert_to_pure_python(self):
#         code_str="from autograms import Autogram, AutogramConfig\n\n"
#         code_str="#set arguments to AutogramConfig to change settings\nconfig=AutogramConfig()\n\n"
#         code_str="#need to load api key dictionary from json file\napi_keys={}"

#         code_str+="autogram = Autogram(config=config,api_keys=api_keys,allow_incomplete=True)\n\n\n"
#         for item in self.node_args:


#             code_str+="#"+item["name"]+ " --> " + ", ".join(item["transitions"])+"\n"
            
#             code_str+="autogram.add_node(\n"

#             for arg in item.keys():
#                 if not item[arg] is None:
#                     if not item[arg]==[]:
#                         code_str+="      "+arg +" = "+repr(item[arg])+",\n"
#             code_str+="      " + ")"
#             code_str+="\n"




#         code_str+="\nautogram.allow_incomplete=False\n"
#         code_str+="autogram.update()"

#         return code_str


#     def convert_to_hybrid_python(self):
#         code_str="\n\n"

#         for item in self.node_args:


#             code_str+="#"+item["name"]+ " --> " + ", ".join(item["transitions"])+"\n"
            
#             code_str+="exec_node(\n"

#             for arg in item.keys():
#                 if not item[arg] is None:
#                     if not item[arg]==[]:
#                         code_str+="      "+arg +" = "+repr(item[arg])+",\n"
#             code_str+="      " + ")"
#             code_str+="\n"

#         return code_str

#     def convert_to_df(self):

#         all_node_set=set()
#         df_node_args=[]
     
#         for node_arg in self.node_args:
#             item = python2df(**node_arg)
#             df_node_args.append(item)
#             for arg in item.keys():
#                 if not item[arg] is None:
#                     if not item[arg]==[]:
#                         all_node_set.add(arg)
#         all_node_set=list(all_node_set)
#         all_node_args=[]


#         fields = 1*EXPECTED_FIELDS
#         # fields.remove("lineno")

#         for field in fields:
#             if field in all_node_set:
#                 all_node_args.append(field)



        
#         df = OrderedDict()
#         for arg in all_node_args:

#             df[arg]=[]

#         for item in df_node_args:
#             for arg in all_node_args:
#                 if arg in item and not item[arg] is None and not item[arg]=="":
#                      df[arg].append(str(item[arg]))
#                 else:
#                     df[arg].append("")
#         return df
    
#     def remove_node(self,node_name):
#         del self.nodes[node_name]

#         for i in range(len(self.node_args)):


#             name1=self.node_args[i]['name']
#             name2=node_name
#             if "(" in name1:
#                 ind = name1.find("(")
#                 name1=name1[:ind]
#             if "(" in name2:
#                 ind = name2.find("(")
#                 name2=name2[:ind]
            
#             if name1==name2:
#                 del self.node_args[i]

#                 return
            










        


            

        





        






