from .base_node import BaseNode

from ..autogram_utils import check_node_req,parse_function,set_variables,get_function


class FunctionNode(BaseNode):
    """
    Node that calls a function
    Corresponds to action = "function"
    This node is reached twice, once when calling a function, and again when returning from the function call.
    This class is for functions with scope "normal", which is the default.
    When calling a function, normal scope functions can see:
        - agent and user replies replies at previous scope (as well as user replies visable to previous scope)
        - variables at previous scope (as well as user replies visable to previous scope)
        - stored states at previous scope (as well as user replies visable to previous scope)
        - any arguments passed to the function
    They cannot see
        - starting prompt at previous scope, this is reset to default prompt

    When returning from a function call of scope normal, the scope the autogram returns to can see:
        - states visited during function call (stored_states)
        - the returned variable

    and cannot see
        - any agent or user replies during the function call
        - any variables set during the function call 


    """
    def __init__(self,autogram_config,statement_interpreter=None,function_type="normal",**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)

        self.function_type = function_type
        self.statement_interpreter=statement_interpreter
    def apply_transition(self,user_reply,memory_object,classifier,nodes,autogram_config):



        if memory_object.is_call() and check_node_req(self,memory_object,include_last=False):
            """
            If it is a function call and the conditions to call the function are met (in check_node_req()), 
            then determine what state is being called as a function, and set the new node id to that state 
            """
          
            instruction = set_variables(self.instruction,memory_object.get_variable_dict(prev_scope=True))
            func=get_function(instruction)
            new_node_id=func


        else:
            """
            Otherwise proceed to next state as normal.
            """
            if self.transition_question is None:
                transition_question=self.transition_question
            else:

                transition_question = set_variables(self.transition_question,memory_object.get_variable_dict())

            start_prompt=""
            turns = memory_object.get_turns()
            input_turns =turns + [{"user_reply":user_reply,  "instruction":""}]

            inputs,outputs,_ = self.make_prompt(input_turns,start_prompt,required_category=None,max_turns=self.transition_context,transition=True,nodes=nodes)


            node_pred = self.predict_next_state(inputs,outputs,classifier,transition_question,memory_object)
       

            new_node_id=node_pred


                




        return new_node_id
    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):
        
        
        
        if memory_object.is_return():
            """
            If we are returning from a function call, we do very little here
            """

            response_to_user=False
            new_user_reply=None
            response=None

            memory_object.append_state(self.name)
            turn_dict = {"retain_instruction":False,"user_reply":"","agent_reply":"","instruction":self.instruction,"state":self.name,"category":self.state_category,"is_reply":False}
            memory_object.append_turn(**turn_dict)
            
            return response,new_user_reply,response_to_user


        else:
            """
            If calling a function, we need to call memory object.manage_call to append the stack to intialize the new scope
            """
            instruction = set_variables(self.instruction,memory_object.get_variable_dict())
            var_name,func,args=parse_function(instruction,memory_object.get_variable_dict(),self.statement_interpreter)

            memory_object.append_state(self.name)
            turn_dict = {"retain_instruction":False,"user_reply":"","agent_reply":"","instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":False}
            memory_object.append_turn(**turn_dict)


            new_args = nodes[func].args


            if check_node_req(self,memory_object,include_last=False):
                variable_dict = dict()
                orig_variable_dict=memory_object.get_variable_dict()
                if len(args)>len(new_args):
                    raise Exception("function called from node " +self.name + " with more arguments than function accepts")
                for i in range(len(args)):
                    variable_dict[new_args[i]] = args[i]
                    


                memory_object.manage_call(variable_dict,self.function_type)

                
            response_to_user=False
            new_user_reply=None
            response=None
            


            return response,new_user_reply,response_to_user
        

    def get_variable_output(self,user_reply,memory_object):

        

        if memory_object.is_return():
            """If we are returning from a function call
            Finalize the return with the memory object, and get the returned variable and output it as this node's variable output
            """
            variable_output=memory_object.finalize_return()

        else:
            variable_output = None
        
        
        return variable_output

        
class LocalFunctionNode(FunctionNode):
    """
    This class is for functions with scope "local", and inherits it's behavior from FunctionNode
    Function with local scope, can only see arguments that are passed to it. 
    When returning, everything besides returned variable is erased in the stack.

    Corresponds to action = "local_function" 

    When calling a function, lcoal scope functions can see:
        - any arguments passed to the function
    They cannot see
        - starting prompt at previous scope, this is reset to default prompt
        - agent and user replies replies at previous scope (as well as user replies visable to previous scope)
        - variables at previous scope (as well as user replies visable to previous scope)
        - stored states at previous scope (as well as user replies visable to previous scope)

    When returning from a function call of scope normal, the scope the autogram returns to can see:
        
        - the returned variable

    and cannot see
        - states visited during function call (stored_states)
        - any agent or user replies during the function call
        - any variables set during the function call 

    Note that if using logging in 'model_turns', you (but not the agent) will still be able to see model inputs and responses during local function calls 
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,function_type="local",**kwargs)




class GlobalFunctionNode(FunctionNode):
    """
    This class is for functions with scope "global", and inherits it's behavior from FunctionNode
    Function with global scope, can see everything in the stack that the calling scope has access too. 
    When returning, all lists (turns and stored states) are appended to previous scope
    all variables and prompts set in global function overwrite previous variables and prompts

    Corresponds to action = "global_function" 

    
    When calling a function, global scope functions can see:
        - any arguments passed to the function
        - starting prompt at previous scope, this is reset to default prompt
        - agent and user replies replies at previous scope (as well as user replies visable to previous scope)
        - variables at previous scope (as well as user replies visable to previous scope)
        - stored states at previous scope (as well as user replies visable to previous scope)

    When returning from a function call of scope normal, the scope the agent returns to can see:
        
        - the returned variable
        - states visited during function call (stored_states)
        - any agent or user replies during the function call
        - any variables set during the function call (will overwrite previous values if same name is used) 
        - any changes made to prompts

    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,function_type="global",**kwargs)



