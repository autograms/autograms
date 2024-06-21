
from .base_node import BaseNode

from ..autogram_utils import check_node_req,parse_function,set_variables,split_assignment
import ast


class PythonFunctionNode(BaseNode):
    """

    """

    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)


        
        
        # var_name,func,args=parse_function(self.instruction)

        # if func[:2] in autogram_config.python_modules.keys():
        #     self.function = autogram_config.python_modules[func[:2]]
        # else:
        #     raise Exception("invalid python function call "+func[:2] + " at node "+self.name)
        
        # if "api_keys" in kwargs.keys():
        #     if self.function in kwargs["api_keys"]:
        #         self.api_key = kwargs["api_keys"][self.function]
        #     else:
        #         self.api_key=None
        # else:
        #     self.api_key=None
        self.modules = autogram_config.python_modules


        # module = ast.parse(self.instruction)

        # fields = dir(module.body[0])

        # if "targets" in fields:
        #     var_name = module.body[0].targets[0].id


        # if isinstance(module.body[0].value,ast.Call):
        #     func = module.body[0].value.func.id

        #     set_args = []

        #     for arg in module.body[0].value.args:
        #         if isinstance(arg,ast.Name):
        #             set_args.append(arg.id)


        #         else:
        #             set_args.append(ast.literal_eval(arg))





        # else:






        # module.body[0].value

        
        



       # isinstance(module.body[0].targets[0],ast.Name)

        #module.body[0].targets[0].id


       # res.body[0].value.func.id
       #res.body[0].value.args[0].id
       #res.body[0].value.args[1].value
       #isinstance((res.body[0].value.args[1]), ast.Name)






            
          



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
    
# class PythonLiteralNode(PythonFunctionNode):
#     def apply_instruction(self,user_reply,memory_object,chatbot,nodes):
#         new_instruction = self.instruction
#         ind = new_instruction.find("=")
#         var_name = new_instruction[:ind].replace(" ","")
        
