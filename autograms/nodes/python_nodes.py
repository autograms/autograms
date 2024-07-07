
from .base_node import BaseNode

from ..autogram_utils import check_node_req,parse_function,set_variables,split_assignment
import ast


class PythonFunctionNode(BaseNode):
    """
    corresponds to action = "python_function"

    Node for executing instruction as python code

    code is executed in statement_interpreter.py with eval function
    """

    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)


        
        

        self.modules = autogram_config.python_modules







            
          



    def get_variable_output(self,user_reply,memory_object):
        
        variable_output = memory_object.pop_python_return()
        return variable_output


    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):
        


        

        variable_dict=memory_object.get_variable_dict()

        var_name,instruction = split_assignment(self.instruction)


        instruction = set_variables(instruction,memory_object.get_variable_dict())



        #can also use pdb.set_trace() directly if pdb in python_imports, but checkpointing here allows memory object to be seen
        if  instruction=="debug_checkpoint()":
            variables=memory_object.get_variable_dict()
            model_turns = memory_object.memory_dict["model_turns"]
            import pdb;pdb.set_trace()
            result=""
       
       
        else:
            if self.statement_interpreter.reference_memory_object:
                variables["_memory_object"]=memory_object

            result=self.statement_interpreter.execute_expression(instruction,variable_dict)
        
        



        memory_object.set_python_return(result)

        response_to_user=False
        new_user_reply=None
        response=None

        memory_object.append_state(self.name)
        turn_dict = {"retain_instruction":False,"user_reply":"","agent_reply":"","instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":False}
        memory_object.append_turn(**turn_dict)
        
        return response,new_user_reply,response_to_user
    

        
