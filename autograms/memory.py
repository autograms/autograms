

#from .__init__ import __version__
import base64

import dill
import threading
import types
import inspect

from datetime import datetime
debug = False
from .autogram_utils.code_utils import SYSTEM_OBJ_NAME,SYSTEM_KWARGS_NAME


from contextvars import ContextVar
from contextlib import contextmanager

# Define a ContextVar for memory
_memory_var = ContextVar("autograms_memory", default=None)

#old logic
#_thread_local = threading.local()


def get_persistent_globals():
    """
    Retrieves persistent global variables stored in thread-local memory.

    Returns:
    - dict: Persistent global variables or an empty dictionary if none exist.
    """

    frame = inspect.currentframe().f_back
    if '_persistent_globals' in frame.f_globals:
        return frame.f_globals['_persistent_globals']
    else:
        return []



def get_timestamp():
    """
    Generates a timestamp for the current time.

    Returns:
    - str: The current timestamp in 'YYYY-MM-DD HH:MM:SS.mmm' format.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    return timestamp




class set_persistent_globals:
    """
    Context manager for defining persistent globals.
    
    Persistent globals are preserved across memory reloads, ensuring continuity of key variables.
    """
    def __enter__(self):
        """
        Captures the initial state of global variables.
        """


        self.frame = inspect.currentframe().f_back

        self.start_globals = self.frame.f_globals.copy()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stores newly defined globals in thread-local memory as persistent.
        """
        print("done setting globals")
        end_globals = self.frame.f_globals
        new_globals = {k: v for k, v in end_globals.items() if k not in self.start_globals}


        end_globals['_persistent_globals'] = list(new_globals.keys())
        end_globals['_persistent_globals_str']= dill.dumps(new_globals)


        


@contextmanager
def use_memory(memory=None):
    """
    Context manager for setting memory in thread-local storage.

    Parameters:
    - memory (SerializableMemory): The memory object to use. Defaults to a new SerializableMemory instance.

    """
    if memory is None:
        memory = SerializableMemory()

    """Set _memory in thread-local storage."""
    token = set_memory(memory)
    
    try:
        yield
    finally:

        reset_memory(token)

            


def get_memory():
    """
    gets the current memory in thread-local storage.

    Returns:
    - memory (SerializableMemory): The memory object currently set or None if no memory object is set.
    """

    return _memory_var.get()


def set_memory(memory):
    """
    Sets the current memory in thread-local storage.

    Parameters:
    - memory (SerializableMemory): The memory object to set.
    """


    """Set _memory in thread-local storage."""
    return _memory_var.set(memory)


def reset_memory(token):
    """
    Resets the memory object to a previous state using a token.

    Parameters:
    - token: A token returned by `set_memory`.
    """
    _memory_var.reset(token)


def clear_memory():
    """
    Clears the current memory object by setting it to None.
    """
    _memory_var.set(None)


   


class UserGlobals():
    def __init__(self):
        self.init_dict = {}



    def _get_thread_dict(self):
        # Initialize the dictionary for the current thread if it doesn't exist

        mem = get_memory()
        if mem is None:
            return self.init_dict
          
        else:
            return mem.memory_dict['user_globals']
        

    def __getitem__(self, key):
        thread_dict = self._get_thread_dict()

        return thread_dict[key]

    def __setitem__(self, key, value):
        thread_dict = self._get_thread_dict()
        thread_dict[key] = value

    def __delitem__(self, key):
        thread_dict = self._get_thread_dict()
        del thread_dict[key]

    def __contains__(self, key):
        thread_dict = self._get_thread_dict()
        return key in thread_dict

    def items(self):
        return self._get_thread_dict().items()

    def keys(self):
        return self._get_thread_dict().keys()

    def values(self):
        return self._get_thread_dict().values()

    def get(self, key, default=None):
        return self._get_thread_dict().get(key, default)

    def clear(self):
        self._get_thread_dict().clear()
    def __repr__(self):
        """
        Returns a string representation of the thread-specific dictionary,
        prefixed with 'UserGlobals'.
        """
        # Convert the underlying dictionary to a normal dict so it prints nicely
        thread_dict = self._get_thread_dict()
        return f"UserGlobals({thread_dict})"
    # def __getattr__(self, name):
    #     """
    #     Called when 'user_globals.name' is accessed and 'name' 
    #     isn't found among normal attributes.
    #     We try to get it from the thread dict.
    #     """
    #     # We want to skip the standard __getattribute__ logic for special 
    #     # attributes like __dict__, __class__, etc. So only 
    #     # unknown names proceed here.
    #     thread_dict = self._get_thread_dict()
    #     if name in thread_dict:
    #         return thread_dict[name]
    #     else:
    #         raise AttributeError(
    #             f"'UserGlobals' object has no attribute '{name}'"
    #         )

    # def __setattr__(self, name, value):
    #     """
    #     Called for 'user_globals.name = value'.
    #     If the attribute 'name' is recognized as a normal class attribute 
    #     (like 'init_dict'), set it normally. Otherwise, store in the thread dict.
    #     """
    #     # We must detect whether 'name' is a normal attribute 
    #     # or something that belongs in the thread dict
    #     # Typically you'd do something like:
    #     if name in ("init_dict", "_get_thread_dict", "items", "keys", 
    #                 "values", "get", "clear", "__repr__",
    #                 "__getattr__", "__setattr__", "__getitem__", 
    #                 "__setitem__", "__delitem__", "__contains__"):
    #         if name in ("items", "keys", "values", "clear", "get"):
    #             raise AttributeError(
    #                 f"Cannot overshadow the built-in method '{name}' with attribute assignment"
    #             )
    #         # It's a real class attribute or method; store normally
    #         super().__setattr__(name, value)
    #     else:
    #         # store in the thread dict
    #         thread_dict = self._get_thread_dict()
    #         thread_dict[name] = value

    # def __delattr__(self, name):
    #     """
    #     If we do 'del user_globals.x', we try removing from the 
    #     thread dict. If not found, we do normal del.
    #     """
    #     # We want to see if 'name' is in the per-thread dictionary
    #     thread_dict = self._get_thread_dict()
    #     if name in thread_dict:
    #         del thread_dict[name]
    #     else:
    #         # it might be a real class-level attribute
    #         super().__delattr__(name)

user_global_modules = dict()
def init_user_globals():
    #use inspect to create unique id (derived from file (if exists, name (if exists), etc. throw exception if user_globals already initialized in this space))
    frame = inspect.currentframe().f_back
    module_globals = frame.f_globals

    # Create a unique module ID
    module_id = create_module_id(module_globals)

    if module_id in user_global_modules:
        raise Exception("User globals can only be initialized once per module")


    user_globals = UserGlobals()
    user_global_modules[module_id] = user_globals
    return user_globals

def create_module_id(module_globals):
    """Create a unique identifier for a module based on its globals."""
    module_file = module_globals.get("__file__", None)
    module_name = module_globals.get("__name__", None)

    if module_file:
        # Use file path as primary identifier
        return f"file::{module_file}"
    elif module_name:
        # Use module name as fallback
        return f"name::{module_name}"
    else:
        # Fallback to unique ID of the globals dictionary
        return f"id::{id(module_globals)}"




class SerializableMemory():
    """
    Base class for managing memory and stack serialization.
    
    Provides non-chatbot-specific functionality for tracking and reloading the call stack.
    
    Attributes:
    - memory_dict (dict): Dictionary storing the memory state.
    - root_function (function): The root function for the memory context.
    """
    def __init__(self,memory_dict,root_function):
        self.root_function=root_function
        
        if memory_dict is None:
            self.memory_dict=dict()
            self.memory_dict['stack']=[]
            self.memory_dict['stack_pointer']=-1
            self.memory_dict['cached_user_reply']=None
            self.memory_dict['call_depth']=0
            self.memory_dict['globals_snapshot']={}

            
        if not 'user_globals' in self.memory_dict:
            module_id = create_module_id(self.root_function.func.__globals__)
            if module_id in user_global_modules:
                self.memory_dict['user_globals']= dill.loads(dill.dumps(user_global_modules[module_id].init_dict))
            else:
                self.memory_dict['user_globals']=dict()


        

        self.globals_snapshot={}
    def set_globals_snapshot(self,):
        """
        Captures a snapshot of current globals for serialization.
        """
        if not '_persistent_globals' in self.root_function.func.__globals__:
            self.memory_dict['globals_snapshot']={} #self.root_function.func.__globals__.copy()
        else:
            persistent_globals= self.root_function.func.__globals__['_persistent_globals']
            self.memory_dict['globals_snapshot']={k: v for k, v in self.root_function.func.__globals__.items() if k in persistent_globals}





    def process_call(self,frame=None):
        """
        Processes a function call, determining whether it's a new call or a reload.

        Parameters:
        - frame (FrameInfo): The current stack frame.

        Returns:
        - tuple: (call_info, include_line), where call_info is function call details or None, and include_line indicates if the call line should be included.
        """


        self.memory_dict['stack_pointer']+=1

        
        include_line=False

        #if (incremented) stack pointer is less  length of stack, we are reloading a function
        if self.memory_dict['stack_pointer']<len(self.memory_dict['stack']):
           
            call_info = self.memory_dict['stack'][self.memory_dict['stack_pointer']]

            #if its not the most recent function, we need to include the line so that the next function after won't be skipped
            if  self.memory_dict['stack_pointer']<(len(self.memory_dict['stack'])-1):
                include_line=True
        #otherwise we are calling a function
        else:
            
            self.memory_dict['call_depth']+=1
            call_info=None


            #if call is coming from outside of autograms, we don't record caller info
            if self.memory_dict['stack_pointer']==0:
                # line_number= None
                # function_name = None
                # code_locals = {}  
                # code_globals =  {}  
                pass
                

            #otherwise we do
            else:

                line_number= frame.frame.f_code.co_firstlineno + frame.frame.f_lineno - 1
                function_name = frame.frame.f_code.co_name
                code_locals = frame.frame.f_locals.copy()
                code_locals.pop(SYSTEM_OBJ_NAME, None)
                code_locals.pop(SYSTEM_KWARGS_NAME, None)
          


                if self.memory_dict['stack_pointer']>len(self.memory_dict['stack']):

                    #this is the stack info for the previous call, the stack will lag 1 behind the new call since we don't have this information yet
                    self.memory_dict['stack'].append({"line_number":line_number,"function_name":function_name,"locals":code_locals})
                else:
                    #import pdb;pdb.set_trace()
                    self.memory_dict['stack'][self.memory_dict['stack_pointer']-1]={"line_number":line_number,"function_name":function_name,"locals":code_locals}




        return call_info,include_line
    

    def process_return(self):

        """
        Handles a function return, updating the stack accordingly.
        """
        
        #if call depth is length of stack, we need to remove top of stack. Otherwise we do not, since it means that the last stack element was never added
        if self.memory_dict['call_depth'] == len(self.memory_dict['stack']):
            self.memory_dict['stack'] = self.memory_dict['stack'][:-1]

        elif not(self.memory_dict['call_depth']-1 == len(self.memory_dict['stack'])):
            raise Exception("Autograms system error, stack length and call depth out of sync during return. This could be a bug.")



        self.memory_dict['stack_pointer']-=1
        self.memory_dict['call_depth']-=1

    def process_function_exit(self,function_name,line_number,code_locals,address=None):
        """
        Logs the state of a function upon exit for serialization.

        Parameters:
        - function_name (str): Name of the function.
        - line_number (int): Line number of the exit point.
        - code_locals (dict): Local variables at the time of exit.
        """
        # print(f"function: {function_name}")
        # print(f"stack pointer: {self.memory_dict['stack_pointer']}")
        # print(f"call depth: {self.memory_dict['call_depth']}")
        # print(f"stack length: {len(self.memory_dict['stack'])}")



        if len(self.memory_dict['stack'])==self.memory_dict['stack_pointer']:
         
             self.memory_dict['stack'].append({"line_number":line_number,"function_name":function_name,"locals":code_locals,"address":address})
        else: 
            self.memory_dict['stack'][self.memory_dict['stack_pointer']] = {"line_number":line_number,"function_name":function_name,"locals":code_locals,"address":address}
        # if len(self.memory_dict['stack'])>0 and not self.memory_dict['stack'][0]['function_name']=='main':
        #     import pdb;pdb.set_trace()
        
        

        if debug:
            
            import pdb;pdb.set_trace()

        

        self.memory_dict['stack_pointer']-=1


    def serialize(self):
        """
        Serializes the memory object.



        Returns:
        - str: Serialized representation of the memory.
        """
        try:
            obj_str = dill.dumps(self.memory_dict)
            obj_base64 = base64.b64encode(obj_str).decode('utf-8')
        except Exception as e:
            # 
            raise type(e)(f"Autograms serialization error. This is most likely caused by using an unserializable local variable in an @autograms_function().Unserializable variables in Python include OS-level handles, dynamically created local objects, and extension objects lacking a pickle protocol. You can most likely solve this issue by initialiazing the problem as a global outside of the @autograms_function() (best practice for variables that are not user-specific), or using it as a local in regular python function called from the @autograms_function. Here is the original error:{str(e)}").with_traceback(e.__traceback__) from e

        return obj_base64

    def save(self,file_name):
        """
        Saves the memory object to a file.

        Parameters:
        - file_name (str): Name of the file to save to.

        """
        with open(file_name,'wb') as fid:
            dill.dump(self.memory_dict,fid)


    # def save(self,file_name,serialization_type="memory_partial"):
    #     save_obj = self.serialilize(serialization_type)
    #     if save_obj =="memory_full":
    #         non_func_globals= get_non_function_globals(self.func)
    #     else:




"""
Keeps track of state of the algorithm
Non-autograms specific python handling of memory and stack happens in super class SerializableMemory
"""

class MemoryObject(SerializableMemory):

    """
    Main memory class for chatbot applications, extending SerializableMemory.

    Adds support for chatbot-specific functionality, including turn management.

    Attributes:
    - config (object): Configuration object for the memory.
    - root_function (AutogramsFunction): initial @autograms_function function that will be called for the chatbot
    - memory_dict (dict): dictionary to initialize memory from
    """

    def __init__(self,config,root_function=None,memory_dict=None,):


        from . import __version__

        self.root_function = root_function
        self.test_mode=False
        self.supervisor_mode=False
     #   self.supervisor_active = False
        self.config=config
        self.last_node=None
    #   self.last_info=None

        if memory_dict is None:
            self.memory_dict=dict()
            self.memory_dict['stack']=[]
            self.memory_dict['turn_stack']=[]
            self.memory_dict['stack_pointer']=-1
            self.memory_dict['cached_user_reply']=None
            self.memory_dict['call_depth']=0
            self.memory_dict['globals_snapshot']={}
            self.memory_dict['external_call_memory']=None
            self.memory_dict['model_turns']=[]

            #we may later use this to maintain backward compatibiltiy if future memory objects have different structure
            self.memory_dict["version"] = __version__

            self.memory_dict['external_call']=None

        else:

            self.memory_dict=memory_dict


        super().__init__(self.memory_dict,self.root_function)

    
        self.default_prompt = config.default_prompt
        self.unused_user_reply=False
       



    def serialize(self):

        """
        Serializes the memory object with chatbot-specific context.


        Returns:
        - str: Serialized representation of the memory.
        """
        try:
            obj_str = dill.dumps(self.memory_dict)
            obj_base64 = base64.b64encode(obj_str).decode('utf-8')
        except Exception as e:
            # 
            raise type(e)(f"'{str(e)}'\nAutograms Serialization Failed. This is most likely caused by using an unserializable local variable in an @autograms_function(). Unserializable variables in Python include OS-level handles, dynamically created local objects, and extension objects lacking a pickle protocol. You can most likely solve this issue by initializing the problem variable as a global outside of the @autograms_function() (best practice for variables that are not user-specific), using it as a local in regular python function called from the @autograms_function()").with_traceback(e.__traceback__) from e

        return obj_base64

    def save(self,file_name):
        """
        Saves the memory object with chatbot-specific context.

        Parameters:
        - file_name (str): Name of the file to save to.
        """
        with open(file_name,'wb') as fid:
            dill.dump(self.memory_dict,fid)


    def set_test_mode(self,test_mode):

        """
        Sets the memory object to test mode.

        Parameters:
        - test_mode (bool): If True, enables test mode.
        """
        self.test_mode=test_mode
    def set_supervisor_mode(self,supervisor_mode):

        self.supervisor_mode=supervisor_mode


    @contextmanager
    def set_node(self,ADDRESS):
        """
        Context manager for setting the current node address for logging.

        Parameters:
        - ADDRESS (str): The node address.
        """
        self.memory_dict['model_turns'].append({"node":ADDRESS,"entry_type":"node","timestamp":get_timestamp()})
        self.last_node=ADDRESS
        #print(f"setting node {ADDRESS}")
        try:
            yield
        finally:
            self.last_node=None

            


    def process_external_call(self):
        if len(self.memory_dict['turn_stack'])>0:
            system_prompt = self.memory_dict['turn_stack'][-1]['system_prompt']
        else:
            system_prompt = self.config.default_prompt
        self.memory_dict['turn_stack'].append({"scope":"normal","turns":[],"system_prompt":system_prompt})

    def process_external_return(self):
        self.memory_dict['turn_stack']=self.memory_dict['turn_stack'][:-1]




    def process_call(self,frame=None,conv_scope="global"):
        """
        Processes a function call, managing chatbot-specific context.

        Parameters:
        - frame (FrameInfo): The current stack frame.
        - conv_scope (str): Conversation scope ('global', 'normal', 'local').

        Returns:
        - tuple: (call_info, include_line).
        """


        call_info,include_line = super().process_call(frame)

        if not self.memory_dict["external_call_memory"] is None:
            include_line=True

        if self.memory_dict['stack_pointer']>=len(self.memory_dict['stack']):
            if len(self.memory_dict['turn_stack'])>0:
               system_prompt = self.memory_dict['turn_stack'][-1]['system_prompt']
            else:
               system_prompt = self.config.default_prompt
               
            self.memory_dict['turn_stack'].append({"scope":conv_scope,"turns":[],"system_prompt":system_prompt})
           
        if self.unused_user_reply:
            self.memory_dict['turn_stack'][-1]["turns"].append({"role":"user","content":self.memory_dict['cached_user_reply']})

            self.unused_user_reply=False



        return call_info,include_line
           





        
        # include_line=False

        # #if (incremented) stack pointer is less  length of stack, we are reloading a function
        # if self.memory_dict['stack_pointer']<len(self.memory_dict['stack']):
           
        #     call_info = self.memory_dict['stack'][self.memory_dict['stack_pointer']]

        #     #if its not the most recent function, we need to include the line so that the next function after won't be skipped
        #     if  self.memory_dict['stack_pointer']<(len(self.memory_dict['stack'])-1):
        #         include_line=True
        # #otherwise we are calling a function
        # else:
            
        #     self.memory_dict['call_depth']+=1
        #     call_info=None


        #     #if call is coming from outside of autograms, we don't record caller info
        #     if self.memory_dict['stack_pointer']==0:
        #         # line_number= None
        #         # function_name = None
        #         # code_locals = {}  
        #         # code_globals =  {}  
        #         pass
                

        #     #otherwise we do
        #     else:

        #         line_number= frame.frame.f_code.co_firstlineno + frame.frame.f_lineno - 1
        #         function_name = frame.frame.f_code.co_name
        #         code_locals = frame.frame.f_locals.copy()  
        #         code_globals =  frame.frame.f_globals.copy()  


        #         if self.memory_dict['stack_pointer']>len(self.memory_dict['stack']):

        #             #this is the stack info for the previous call, the stack will lag 1 behind the new call since we don't have this information yet
        #             self.memory_dict['stack'].append({"line_number":line_number,"function_name":function_name,"locals":code_locals,"globals":code_globals,"scope":variable_scope})
        #         else:
        #             #import pdb;pdb.set_trace()
        #             self.memory_dict['stack'][self.memory_dict['stack_pointer']-1]={"line_number":line_number,"function_name":function_name,"locals":code_locals,"globals":code_globals,"scope":variable_scope}

                
        #         # if len(self.memory_dict['stack'])>1:
        #         #     import pdb;pdb.set_trace()

            
            
        #     self.memory_dict['turn_stack'].append({"scope":conv_scope,"turns":[]})
            
        # globals_to_add=dict()
        # for item in reversed(self.memory_dict['stack'][:self.memory_dict['stack_pointer']]):
        #     #if item['scope']=="local":
        #     break

        #     for key in item['code_locals']:
        #         if not key in globals_to_add:
        #             globals_to_add[key]=item['code_locals'][key]
            



        # return call_info,include_line,globals_to_add
    def process_return(self):
        """
        Handles a function return, updating chatbot-specific state.
        """
        super().process_return()

        
        #pop turn stack and append to previous layer
        if self.memory_dict['turn_stack'][-1]['scope']=="global":
            if len(self.memory_dict['turn_stack'])>1:
                for turn in self.memory_dict['turn_stack'][-1]['turns']:
                    self.memory_dict['turn_stack'][-2]['turns'].append(turn)



        self.memory_dict['turn_stack']=self.memory_dict['turn_stack'][:-1]



    def add_user_reply(self,user_reply):
        """
        Logs a user's reply in the conversation.

        Parameters:
        - user_reply (str): The user's reply.
        """
        self.memory_dict['model_turns'].append({"user_reply":user_reply,"entry_type":"user_reply","timestamp":get_timestamp()})

        if not user_reply is None and len(user_reply)>0:
            if len(self.memory_dict['turn_stack'])>0:
                self.memory_dict['turn_stack'][-1]['turns'].append({"role":"user","content":user_reply})
            else:
                self.unused_user_reply=True

            self.memory_dict["cached_user_reply"]=user_reply
    def get_user_reply(self):
        return self.memory_dict["cached_user_reply"]
    def get_turns_for_model(self,instruction=None):

        """
        Retrieves conversation turns for model input.

        Parameters:
        - instruction (str): Instruction for the model.

        Returns:
        - tuple: (turns, system_prompt).
        """

        turns=[]
        cached_user_reply=self.memory_dict['cached_user_reply']
        for i in reversed(range(len(self.memory_dict['turn_stack']))):


            turns = self.memory_dict['turn_stack'][i]['turns'] + turns

            scope = self.memory_dict['turn_stack'][i]['scope']



            if scope=="local":
                break

       # turns.append({"user_reply":cached_user_reply, "instruction":instruction})
        system_prompt = self.memory_dict['turn_stack'][-1]['system_prompt']

        

        return turns,system_prompt



    def extract_full_conv_history(self):

        conv_turns = []
        for turn in self.memory_dict['model_turns']:
            if turn["entry_type"]=="agent_reply":
                conv_turns.append({"role":"assistant","content":turn["reply"]})

            if turn["entry_type"]=="user_reply":
                conv_turns.append({"role":"user","content":turn["user_reply"]})
        return conv_turns
    
    def extract_conv_history_str(self):
        out_str=""
        turns = self.extract_full_conv_history()
        for turn in turns:
            out_str+=f"{turn['role']}: {turn['content']}\n\n"
        return out_str








    def log_chat_turn(self,reply,instruction=None,retain_instruction=False,line_number=None,function_name=None):
        """
        Logs a chatbot turn with user and agent interactions.

        Parameters:
        - reply (str): Chatbot's reply.
        - instruction (str): Instruction for the turn.
        - retain_instruction (bool): Whether to retain the instruction.
        - line_number (int): Line number of the turn.
        - function_name (str): Function name of the turn.
        """

        if self.memory_dict['cached_user_reply'] is None:
            user_reply = None
        else:
            user_reply = self.memory_dict['cached_user_reply']
            self.memory_dict['cached_user_reply']=None

        self.memory_dict['turn_stack'][-1]['turns'].append({"role":"agent","content":reply})
        self.memory_dict['model_turns'].append({"reply":reply,"entry_type":"agent_reply","last_node":self.last_node,"line_number":line_number,"function_name":function_name,"timestamp":get_timestamp()})

    def log_thought_turn(self,reply,instruction,retain_instruction=True):

        """
        Logs a thought turn (internal reasoning).

        Parameters:
        - reply (str): Thought output.
        - instruction (str): Thought instruction.
        - retain_instruction (bool): Whether to retain the instruction.
        """

        user_reply = None

        self.memory_dict['turn_stack'][-1]['turns'].append({"role":"system_instruction","content":instruction})
        self.memory_dict['turn_stack'][-1]['turns'].append({"role":"system_answer","content":reply})


    def set_system_prompt(self,text):
        """
        Sets the system prompt for the conversation.

        Parameters:
        - text (str): The system prompt text.
        """
        self.memory_dict['turn_stack'][-1]["system_prompt"]=text


    def get_system_prompt(self):

        return self.memory_dict['turn_stack'][-1]["system_prompt"]
  

    
    def log_classifier_turn(self,result,input_turns,output_turns,answer_choices,usage_log=None,system_prompt=None):
        """
        Logs a classifier turn.

        Parameters:
        - result (str): Classifier output.
        - input_str (str): Input string for the classifier.
        - answer_choices (list): Possible answers.
        - model_type (str): Type of model used.
        """
        self.memory_dict['model_turns'].append({"output":result,"entry_type":"classifier","input_turns":input_turns,"output_turns":output_turns,"answer_choices":answer_choices,"system_prompt":system_prompt,"usage_log":usage_log,"last_node":self.last_node,"timestamp":get_timestamp()})


    def log_chatbot_turn(self,result,input_turns,output_turns,system_prompt="",usage_log=None):
        """
        Logs a chatbot turn with model input/output.

        Parameters:
        - result (str): Chatbot output.
        - content(str): conversation history
        - system_prompt (str): System prompt.
        - model_type (str): Type of model used.
        """


        self.memory_dict['model_turns'].append({"output":result,"entry_type":"chatbot","input_turns":input_turns,"output_turns":output_turns,"system_prompt":system_prompt,"usage_log":usage_log,"last_node":self.last_node,"timestamp":get_timestamp()})
       

    def log_model_turn(self,result,function_name,function_inputs,code_position=None,supervisor_info=None,usage_log=None):
        """
        Logs a chatbot turn with model input/output.

        Parameters:
        - result (str): Chatbot output.
        - content(str): conversation history
        - system_prompt (str): System prompt.
        - model_type (str): Type of model used.
        """
  
        

  
        self.memory_dict['model_turns'].append({"output":result,"entry_type":"model","function_name":function_name,"function_inputs":function_inputs,"code_position":code_position,"usage_log":usage_log,"supervisor_info":supervisor_info,"timestamp":get_timestamp()})
        # if not self.supervisor_active:
        #     self.last_info=None
       

    
    

class SimpleMemory():
    """
    Lightweight memory class for prompt management without serialization.

    Attributes:
    - config (object): Configuration object for the memory.
    - memory_dict (dict): Dictionary storing conversation turns.
    """

    def __init__(self,config,memory_dict=None):
        self.config=config
        self.test_mode=False
        self.supervisor_mode=False
  #      self.supervisor_active=False
     #   self.last_info=None
        if memory_dict is None:
            self.memory_dict= {"model_turns":[],"turns":[],"system_prompt":self.config.default_prompt,"cached_user_reply":None}


    def set_system_prompt(self,text):
        """
        Sets the system prompt for the conversation.

        Parameters:
        - text (str): The system prompt text.
        """
        self.memory_dict["system_prompt"]=text
    def set_supervisor_mode(self,supervisor_mode):

        self.supervisor_mode=supervisor_mode

    def set_test_mode(self,test_mode):

        """
        Sets the memory object to test mode.

        Parameters:
        - test_mode (bool): If True, enables test mode.
        """
        self.test_mode=test_mode

    def log_chat_turn(self,reply,instruction=None,retain_instruction=False,line_number=None,function_name=None):
        """
        Logs a chatbot turn with user and agent interactions.

        Parameters:
        - reply (str): Chatbot's reply.
        - instruction (str): Instruction for the turn.
        - retain_instruction (bool): Whether to retain the instruction.
        - line_number (int): Line number of the turn.
        - function_name (str): Function name of the turn.
        """

        if self.memory_dict['cached_user_reply'] is None:
            user_reply = None
        else:
            user_reply = self.memory_dict['cached_user_reply']
            self.memory_dict['cached_user_reply']=None

        self.memory_dict['turns'].append({"role":"agent","content":reply})
        self.memory_dict['model_turns'].append({"reply":reply,"entry_type":"agent_reply","last_node":self.last_node,"line_number":line_number,"function_name":function_name,"timestamp":get_timestamp()})

    def log_thought_turn(self,reply,instruction,retain_instruction=True):

        """
        Logs a thought turn (internal reasoning).

        Parameters:
        - reply (str): Thought output.
        - instruction (str): Thought instruction.
        - retain_instruction (bool): Whether to retain the instruction.
        """

        user_reply = None

        self.memory_dict['turns'].append({"role":"system_instruction","content":instruction})
        self.memory_dict['turns'].append({"role":"system_answer","content":reply})

    def log_classifier_turn(self,result,input_turns,output_turns,answer_choices,usage_log=None,system_prompt=None):
        """
        Logs a classifier turn.

        Parameters:
        - result (str): Classifier output.
        - input_str (str): Input string for the classifier.
        - answer_choices (list): Possible answers.
        - model_type (str): Type of model used.
        """
        self.memory_dict['model_turns'].append({"output":result,"entry_type":"classifier","input_turns":input_turns,"output_turns":output_turns,"answer_choices":answer_choices,"system_prompt":system_prompt,"usage_log":usage_log,"last_node":None,"timestamp":get_timestamp()})


    def log_chatbot_turn(self,result,input_turns,output_turns,system_prompt="",usage_log=None):
        """
        Logs a chatbot turn with model input/output.

        Parameters:
        - result (str): Chatbot output.
        - content(str): conversation history
        - system_prompt (str): System prompt.
        - model_type (str): Type of model used.
        """


        self.memory_dict['model_turns'].append({"output":result,"entry_type":"chatbot","input_turns":input_turns,"output_turns":output_turns,"system_prompt":system_prompt,"usage_log":usage_log,"last_node":None,"timestamp":get_timestamp()})
       
    def log_model_turn(self,result,function_name,function_inputs,code_position=None, supervisor_info=None,usage_log=None):
        """
        Logs a chatbot turn with model input/output.

        Parameters:
        - result (str): Chatbot output.
        - content(str): conversation history
        - system_prompt (str): System prompt.
        - model_type (str): Type of model used.
        """

        self.memory_dict['model_turns'].append({"output":result,"entry_type":"model","function_name":function_name,"function_inputs":function_inputs,"usage_log":usage_log,"supervisor_info":supervisor_info,"timestamp":get_timestamp()})
        # if not self.supervisor_active:
        #     self.last_info=None
    def add_user_reply(self,user_reply):
        """
        Logs a user's reply in the conversation.

        Parameters:
        - user_reply (str): The user's reply.
        """
        self.memory_dict['model_turns'].append({"user_reply":user_reply,"entry_type":"user_reply","timestamp":get_timestamp()})

        if not user_reply is None and len(user_reply)>0:
           
            self.memory_dict['turns'].append({"role":"user","content":user_reply})


            self.memory_dict["cached_user_reply"]=user_reply
    
    def get_turns_for_model(self,instruction=None):
        """
        Retrieves conversation turns for model input.

        Parameters:
        - instruction (str): Instruction for the model.

        Returns:
        - tuple: (turns, system_prompt).
        """
        turns=[]
        cached_user_reply=self.memory_dict['cached_user_reply']

        turns = 1*self.memory_dict['turns'] 



        #turns.append({"user_reply":cached_user_reply, "instruction":instruction})
        system_prompt = self.memory_dict['system_prompt']
        

        return turns,system_prompt

