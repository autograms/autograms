
default_system_globals = globals().keys()

#from .__init__ import __version__
import base64

import dill
import threading
import types
import inspect
from contextlib import contextmanager
from datetime import datetime
debug = False


_thread_local = threading.local()


def get_persistent_globals():
    """
    Retrieves persistent global variables stored in thread-local memory.

    Returns:
    - dict: Persistent global variables or an empty dictionary if none exist.
    """
    if hasattr(_thread_local, 'memory'):
        return _thread_local.memory.persistent_globals
    elif hasattr(_thread_local, 'persistent_globals'):
        return _thread_local.persistent_globals
    else:
        return {}
        

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
        end_globals = self.frame.f_globals
        new_globals = {k: v for k, v in end_globals.items() if k not in self.start_globals}
        if hasattr(_thread_local, 'memory'):
            _thread_local.memory.persistent_globals= new_globals
        else:
            _thread_local.persistent_globals = new_globals


        


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
    set_memory(memory)
    
    try:
        yield
    finally:
        clear_memory()


def set_memory(memory):
    """
    Sets the current memory in thread-local storage.

    Parameters:
    - memory (SerializableMemory): The memory object to set.
    """


    """Set _memory in thread-local storage."""
    _thread_local.memory = memory


def get_memory():
    """
    Retrieves the current memory object from thread-local storage.

    Returns:
    - SerializableMemory or None: The memory object, or None if no memory is set.
    """
    """Retrieve _memory from thread-local storage."""
    return getattr(_thread_local, 'memory', None)

def clear_memory():
    """
    Clears the current memory object from thread-local storage.
    """
    if hasattr(_thread_local, 'memory'):

        del _thread_local.memory

    if hasattr(_thread_local, 'persistent_globals'):
        del _thread_local.persistent_globals




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



        if hasattr(_thread_local, 'persistent_globals'):
            self.persistent_globals = _thread_local.persistent_globals
            del _thread_local.persistent_globals


        else:

            self.persistent_globals={}

        self.globals_snapshot={}
    def set_globals_snapshot(self,):
        """
        Captures a snapshot of current globals for serialization.
        """
        if self.persistent_globals is None:
            self.memory_dict['globals_snapshot']=self.root_function.func.__globals__.copy()
        else:
            self.memory_dict['globals_snapshot']={k: v for k, v in self.root_function.func.__globals__.items() if self.persistent_globals is None or k in self.persistent_globals}



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
                code_globals =  frame.frame.f_globals.copy()  


                if self.memory_dict['stack_pointer']>len(self.memory_dict['stack']):

                    #this is the stack info for the previous call, the stack will lag 1 behind the new call since we don't have this information yet
                    self.memory_dict['stack'].append({"line_number":line_number,"function_name":function_name,"locals":code_locals,"globals":code_globals})
                else:
                    #import pdb;pdb.set_trace()
                    self.memory_dict['stack'][self.memory_dict['stack_pointer']-1]={"line_number":line_number,"function_name":function_name,"locals":code_locals,"globals":code_globals}




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

    def process_function_exit(self,function_name,line_number,code_locals):
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
         
             self.memory_dict['stack'].append({"line_number":line_number,"function_name":function_name,"locals":code_locals})
        else: 
            self.memory_dict['stack'][self.memory_dict['stack_pointer']] = {"line_number":line_number,"function_name":function_name,"locals":code_locals}
        # if len(self.memory_dict['stack'])>0 and not self.memory_dict['stack'][0]['function_name']=='main':
        #     import pdb;pdb.set_trace()
        
        

        if debug:
            
            import pdb;pdb.set_trace()

        

        self.memory_dict['stack_pointer']-=1


    def serialize(self,serialization_type="partial"):
        """
        Serializes the memory object.

        Parameters:
        - serialization_type (str): Type of serialization ('full', 'partial', or 'json').

        Returns:
        - str: Serialized representation of the memory.
        """

        if serialization_type=="full":
            obj_str = dill.dumps(self)
            obj_base64 = base64.b64encode(obj_str).decode('utf-8')
            return obj_str


        else:
            
           # non_function_globals = {k: v for k, v in self.root_function.func.__globals__.items() if self.persistent_globals is None or k in self.persistent_globals}
            
            # {
            #         name: value for name, value in self.root_func.__globals__.items()
            #         if not isinstance(value, (types.FunctionType, types.ModuleType, type))
            #     }
           # obj = {"memory":self.memory_dict,"non_func_globals":self.globals_snapshot }
            if serialization_type=="partial":
                
                obj_str = dill.dumps(self.memory_dict)
                obj_base64 = base64.b64encode(obj_str).decode('utf-8')

                return obj_base64

                

            elif serialization_type=="json":
                raise NotImplementedError("json serialization not implemented yet, use partial for now")
                result = jsonpickle.encode(self.memory_dict)
                return result

    def save(self,file_name,serialization_type="partial"):
        """
        Saves the memory object to a file.

        Parameters:
        - file_name (str): Name of the file to save to.
        - serialization_type (str): Type of serialization ('full', 'partial', or 'json').
        """

        if serialization_type=="full":
            with open(file_name,'wb') as fid:
                dill.dump(self,fid)
            

        else:
            
            # non_function_globals = {
            #         name: value for name, value in self.root_func.__globals__.items()
            #         if not isinstance(value, (types.FunctionType, types.ModuleType, type))
            #     }

           # non_function_globals = {k: v for k, v in self.root_function.func.__globals__.items() if self.persistent_globals is None or k in self.persistent_globals}
        #    obj = {"memory":self.memory_dict,"non_func_globals":self.globals_snapshot }
            if serialization_type=="partial":
                
                with open(file_name,'wb') as fid:
                    dill.dump(self.memory_dict,fid)


            
            elif serialization_type=="json":
                raise NotImplementedError("json serialization not implemented yet, use partial for now")
                result = jsonpickle.encode(self.memory_dict)
                with open(file_name,'w') as fid:
                    fid.write(result)
                

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
        self.config=config
        self.last_node=None
        



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
       



    def serialize(self,serialization_type="partial"):

        """
        Serializes the memory object with chatbot-specific context.

        Parameters:
        - serialization_type (str): Type of serialization ('full', 'partial', or 'json').

        Returns:
        - str: Serialized representation of the memory.
        """
        if serialization_type=="full":
            obj_str = dill.dumps(self)
            obj_base64 = base64.b64encode(obj_str).decode('utf-8')
            return obj_str


        else:
  
            if serialization_type=="partial":
                
                obj_str = dill.dumps(self.memory_dict)
                obj_base64 = base64.b64encode(obj_str).decode('utf-8')

                return obj_base64

                

            elif serialization_type=="json":
                result = jsonpickle.encode(self.memory_dict)
                return result

    def save(self,file_name,serialization_type="partial"):
        """
        Saves the memory object with chatbot-specific context.

        Parameters:
        - file_name (str): Name of the file to save to.
        - serialization_type (str): Type of serialization ('full', 'partial', or 'json').
        """

        if serialization_type=="full":
            with open(file_name,'wb') as fid:
                dill.dump(self,fid)
            

        else:
            

            if serialization_type=="partial":
                
                with open(file_name,'wb') as fid:
                    dill.dump(self.memory_dict,fid)


            
            elif serialization_type=="json":
                result = jsonpickle.encode(self.memory_dict)
                with open(file_name,'w') as fid:
                    fid.write(result)

    def set_test_mode(self,test_mode):

        """
        Sets the memory object to test mode.

        Parameters:
        - test_mode (bool): If True, enables test mode.
        """
        self.test_mode=test_mode


    @contextmanager
    def set_node(self,ADDRESS):
        """
        Context manager for setting the current node address for logging.

        Parameters:
        - ADDRESS (str): The node address.
        """
        self.last_node=ADDRESS
        #print(f"setting node {ADDRESS}")
        try:
            yield
        finally:
            self.last_node=None

            





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
           self.memory_dict['turn_stack'].append({"scope":conv_scope,"turns":[],"system_prompt":self.config.default_prompt})
           


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
        for i in reversed(range(len(self.memory_dict['turn_stack']))):


            turns = self.memory_dict['turn_stack'][i]['turns'] + turns

            scope = self.memory_dict['turn_stack'][i]['scope']




            if scope=="local":
                break

        turns.append({"user_reply":cached_user_reply, "instruction":instruction})
        system_prompt = self.memory_dict['turn_stack'][-1]['system_prompt']
        

        return turns,system_prompt






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

        self.memory_dict['turn_stack'][-1]['turns'].append({"user_reply":user_reply,"agent_reply":reply,"instruction":instruction,"retain_instruction":retain_instruction})
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

        self.memory_dict['turn_stack'][-1]['turns'].append({"user_reply":user_reply,"agent_reply":reply,"instruction":instruction,"retain_instruction":retain_instruction})


    def set_system_prompt(self,text):
        """
        Sets the system prompt for the conversation.

        Parameters:
        - text (str): The system prompt text.
        """
        self.memory_dict['turn_stack'][-1]["system_prompt"]=text



    def log_classifier_turn(self,result,input_str,answer_choices,model_type):
        """
        Logs a classifier turn.

        Parameters:
        - result (str): Classifier output.
        - input_str (str): Input string for the classifier.
        - answer_choices (list): Possible answers.
        - model_type (str): Type of model used.
        """
        self.memory_dict['model_turns'].append({"output":result,"entry_type":"classifier","content":input_str,"answer_choices":answer_choices,"model_type":model_type,"last_node":self.last_node,"timestamp":get_timestamp()})


    def log_chatbot_turn(self,result,input_turns=[],output_turns=[],system_prompt=[],model_type="no_model"):
        """
        Logs a chatbot turn with model input/output.

        Parameters:
        - result (str): Chatbot output.
        - input_turns (list): Input conversation turns.
        - output_turns (list): Output conversation turns.
        - system_prompt (str): System prompt.
        - model_type (str): Type of model used.
        """
        
        self.memory_dict['model_turns'].append({"output":result,"entry_type":"chatbot","input_turns":input_turns,"output_turns":output_turns,"system_prompt":system_prompt,"model_type":model_type,"last_node":self.last_node,"timestamp":get_timestamp()})
       

        

    

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
        if memory_dict is None:
            self.memory_dict= {"model_turns":[],"turns":[],"system_prompt":self.config.default_prompt,"cached_user_reply":None}


    def set_system_prompt(self,text):
        """
        Sets the system prompt for the conversation.

        Parameters:
        - text (str): The system prompt text.
        """
        self.memory_dict["system_prompt"]=text

    def log_chat_turn(self,reply,instruction=None,retain_instruction=False,line_number=None,function_name=None):
        """
        Logs a chatbot turn for SimpleMemory.

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

        self.memory_dict['turns'].append({"user_reply":user_reply,"agent_reply":reply,"instruction":instruction,"retain_instruction":retain_instruction})
       # self.memory_dict['model_turns'].append({"reply":reply,"entry_type":"agent_reply","last_node":self.last_node,"line_number":line_number,"function_name":function_name,"timestamp":get_timestamp()})

    def log_thought_turn(self,reply,instruction,retain_instruction=True):

        """
        Logs a thought turn for SimpleMemory.

        Parameters:
        - reply (str): Thought output.
        - instruction (str): Thought instruction.
        - retain_instruction (bool): Whether to retain the instruction.
        """

        user_reply = None

        self.memory_dict['turn_stack'][-1]['turns'].append({"user_reply":user_reply,"agent_reply":reply,"instruction":instruction,"retain_instruction":retain_instruction})
    

    def log_classifier_turn(self,result,input_str,answer_choices,model_type):
        """
        Logs a classifier turn for SimpleMemory.

        Parameters:
        - result (str): Classifier output.
        - input_str (str): Input string for the classifier.
        - answer_choices (list): Possible answers.
        - model_type (str): Type of model used.
        """
        
        self.memory_dict['model_turns'].append({"output":result,"entry_type":"classifier","content":input_str,"answer_choices":answer_choices,"model_type":model_type,"last_node":None,"timestamp":get_timestamp()})


    def log_chatbot_turn(self,result,input_turns=[],output_turns=[],system_prompt=[],model_type="no_model"):
        """
        Logs a chatbot turn for SimpleMemory.

        Parameters:
        - result (str): Chatbot output.
        - input_turns (list): Input conversation turns.
        - output_turns (list): Output conversation turns.
        - system_prompt (str): System prompt.
        - model_type (str): Type of model used.
        """
        
        self.memory_dict['model_turns'].append({"output":result,"entry_type":"chatbot","input_turns":input_turns,"output_turns":output_turns,"system_prompt":system_prompt,"model_type":model_type,"last_node":None,"timestamp":get_timestamp()})
       

    def add_user_reply(self,user_reply):
        """
        Logs a user's reply in the conversation.

        Parameters:
        - user_reply (str): The user's reply.
        """

     #   self.memory_dict['model_turns'].append({"user_reply":user_reply,"entry_type":"user_reply","timestamp":get_timestamp()})

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



        turns.append({"user_reply":cached_user_reply, "instruction":instruction})
        system_prompt = self.memory_dict['system_prompt']
        

        return turns,system_prompt

