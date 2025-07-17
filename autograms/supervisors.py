

# from .functional import thought,silent_thought, yes_or_no,multiple_choice, reply_instruction
# from .functional import generate_list_of_dicts, generate_list,generate_list_of_choices, generate_fixed_dict,generate_fixed_list
from .program_control import ReplyExit, FunctionExit, GoTo, ReturnTo, ReturnToContinued
from .memory import get_memory
import json

import functools

# def score_result(score):
#     memory = get_memory()
#     memory.last_info = {"score":score}

class SupervisorReturn():
    def __init__(self,output,score = None,rejected_output=None,tags=None):
        self.output = output
        self.score = score
        self.rejected_output = rejected_output
        if tags is None:
            self.tags = []
        else:
            self.tags = tags
  



def supervisable(function_type):

    def _decorator(base_function):
        

       # @functools.wraps(base_function)
        def wrapper(*args, **kwargs):
            # Extract supervisor from kwargs if it exists
     
            supervisor = kwargs.pop('supervisor', None)
            supervisor_kwargs = kwargs.pop('supervisor_kwargs', {})


            memory = get_memory()
            result=None
            
            if memory.supervisor_mode and not(supervisor is None):
                memory.supervisor_active=True

                memory.process_external_call()
               # result=None
                supervisor_call_kwargs = {**kwargs, **supervisor_kwargs}
                try:
                    initial_output = supervisor(*args, **supervisor_call_kwargs)
                    if initial_output is None:
                        raise Exception("no result returned by supervisor")
                    
                    if isinstance(initial_output,SupervisorReturn):
                        function_output = initial_output.output
                        rejected=initial_output.rejected_output
                        score = initial_output.score
                        tags = initial_output.tags
                    else:
                        function_output = initial_output
                        score=None
                        rejected=None
                        tags = None

                    if type(function_output)==str:
                        result = function_output

                    elif function_type =='json':
                        
                        try:
                            result_json = json.dumps(function_output)
                            if len(result_json)>0:
                                result = result_json
                        except:
                            pass


                    elif function_type == 'boolean':
                        if type(function_output)==bool:
                            if function_output:
                                result="Yes"
                            else:
                                result="No"

                    elif function_type == 'selection':
                        if type(function_output)==int:
                            if "choices" in kwargs:
                                choices = kwargs["choices"]
                            else:
                                choices =args[1]
                                if not type(choices)==list:
                                    raise Exception("call to supervisor wrapper for multiple_choice missing choices argument")
                            if function_output>=len(choices):
                                raise Exception("call to supervisor wrapper returned index out of range for choices")
                            result = choices[function_output]

                            if not type(result)==str:
                                raise Exception("invalid option passed for choices argument")
                    


                        # for turn in reversed(memory.memory_dict['model_turns']):
                        #     if turn['entry_type']=="model":
                        #         result = turn['output']

                    

                except ReplyExit as reply_exc:
                    memory.supervisor_active=False
                    memory.process_external_return()
            
                    raise Exception("ReplyExit not allowed in supervisor. To supervise a reply_instruction(), just have the supervisor return a string")  
                        
                
                except FunctionExit as exc_cont:
                    memory.supervisor_active=False
                    memory.process_external_return()   
                    raise Exception("Invalid FunctionExit inside supervisor. This is disallowed. Only ReplyExit can be used in supervisor")  
                    
                except ReturnTo as rt_exc:
                    memory.supervisor_active=False
                    memory.process_external_return()    
                    raise Exception("Invalid RETURNTO inside supervisor. This is disallowed.") 
                    
                except ReturnToContinued as rt_exc:
                    memory.supervisor_active=False
                    memory.process_external_return()    
                    raise Exception("Invalid RETURNTO continued inside supervisor. This is disallowed.") 


                except GoTo as jump_exc:
                    memory.supervisor_active=False
                    memory.process_external_return()    
                    raise Exception("Invalid GOTO inside @supervisor. This is disallowed.") 
                except Exception as e:
                    memory.supervisor_active=False
                    memory.process_external_return()    
                    raise 

                memory.supervisor_active=False
                memory.process_external_return()
                if result is None:
                    raise Exception(f"Unable to parse output of @supervisor function to match output of base function: {base_function}")
            # Execute the custom function
            


                kwargs["_forced_output"]= result
                kwargs["_supervisor_info"]={"score":score,"rejected_output":rejected,"tags":tags}

                    


                return base_function(*args, **kwargs)

            else:
                # Fallback to the original base function
                return base_function(*args, **kwargs)


        
        return wrapper
    return _decorator

# def supervisor(base_function):
#     """
#     Decorator that wraps the user's custom function so that calling
#     it either uses the custom logic or falls back to the base function,
#     depending on config.call_custom.
#     """
#     if base_function not in ALLOWED_BASE_FUNCTIONS:
#         raise ValueError(f"Base function {base_function.__name__} is not allowed for autograms supervisor.")

    

#     def decorator(custom_function):
#         @functools.wraps(custom_function)
#         def wrapper(*args, **kwargs):

#             memory = get_memory()
#             # Decide which function to call based on config
#             if memory.supervisor_mode:
#                 memory.supervisor_active=True

#                 memory.process_external_call()
#                 result=None
#                 try:
#                     function_output = custom_function(*args, **kwargs)
#                     if type(function_output)==str:
#                         result = function_output
#                     elif base_function in STRUCTURE_FUNCTIONS:
                       
#                         try:
#                             result_json = json.dumps(function_output)
#                             if len(result_json)>0:
#                                 result = result_json
#                         except:
#                             pass


#                     elif base_function == yes_or_no:
#                         if type(function_output)==bool:
#                             if function_output:
#                                 result="Yes"
#                             else:
#                                 result="No"

#                     elif base_function == multiple_choice:
#                         if type(function_output)==int:
#                             if "choices" in kwargs:
#                                 choices = kwargs["choices"]
#                             else:
#                                 choices =args[1]
#                                 if not type(choices)==list:
#                                     raise Exception("call to @supervisor wrapper for multiple_choice missing choices argument")
#                             if function_output>=len(choices):
#                                 raise Exception("call to @supervisor wrapper returned index out of range for choices")
#                             result = choices[function_output]

#                             if not type(result)==str:
#                                 raise Exception("invalid option passed for choices argument")

#                     if result is None:

#                         for turn in reversed(memory.memory_dict['model_turns']):
#                             if turn['entry_type']=="model":
#                                 result = turn['output']

                    
                            



#                 except ReplyExit as reply_exc:
#                     memory.supervisor_active=False
#                     memory.process_external_return()
#                     if not base_function == reply_instruction:
#                         raise Exception("ReplyExit only allowed in supervisor if base_function = autograms.functional.reply_instruction")  
                        
#                     result = memory.memory_dict['model_turns'][-1]['output']
                    
                
#                 except FunctionExit as exc_cont:
#                     memory.supervisor_active=False
#                     memory.process_external_return()   
#                     raise Exception("Invalid FunctionExit inside @supervisor. This is disallowed. Only ReplyExit can be used in supervisor")  
                    
#                 except ReturnTo as rt_exc:
#                     memory.supervisor_active=False
#                     memory.process_external_return()    
#                     raise Exception("Invalid RETURNTO inside @supervisor. This is disallowed.") 
                    
#                 except ReturnToContinued as rt_exc:
#                     memory.supervisor_active=False
#                     memory.process_external_return()    
#                     raise Exception("Invalid RETURNTO continued inside @supervisor. This is disallowed.") 


#                 except GoTo as jump_exc:
#                     memory.supervisor_active=False
#                     memory.process_external_return()    
#                     raise Exception("Invalid GOTO inside @supervisor. This is disallowed.") 
#                 except Exception as e:
#                     memory.supervisor_active=False
#                     memory.process_external_return()    
#                     raise 

#                 memory.supervisor_active=False
#                 memory.process_external_return()
#                 if result is None:
#                     raise Exception(f"Unable to parse output of @supervisor function to match output of base function: {base_function}")
#                 # Execute the custom function

#                 kwargs["_force_output"]= {"result":result}

#                 if "supervisor_kwargs" in kwargs:
#                     del kwargs["supervisor_kwargs"]
#                 return base_function(*args, **kwargs)

#             else:
#                 # Fallback to the original base function
#                 return base_function(*args, **kwargs)



#         return wrapper

#     return decorator




