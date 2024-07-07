from .base_node import BaseNode
from ..autogram_utils import set_variables, apply_chatbot
class ThoughtNode(BaseNode):
    """
    corresponds to action = 'thought'

    This is useful when we want the model to set a variable or use internal dialgoue to reason. 
    Model follows instruction, but result is not output to user
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)

    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):

        instruction = set_variables(self.instruction,memory_object.get_variable_dict())


        required_text=""

        start_prompt=memory_object.get_prompt()
        turns = memory_object.get_turns()
        input_turns =turns + [{"user_reply":user_reply, "instruction":instruction}]

        inputs,outputs,prefix = self.make_prompt(input_turns,start_prompt,required_category=self.conv_scope,transition=False,nodes=nodes)

        
        response,success=apply_chatbot(chatbot,memory_object,inputs,outputs,prefix,required_text,self.name)



        memory_object.append_state(self.name)



        turn_dict = {"retain_instruction":True,"user_reply":user_reply,"agent_reply":response,"instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":False,"is_thought":True}
        memory_object.append_turn(**turn_dict)


        response_to_user=False



        #set for any node that consumes input
        new_user_reply=""





        return response,new_user_reply,response_to_user


class ThoughtQANode(ThoughtNode):
    """
    Inherits from most behavior ThoughtNode
    corresponds to action = 'thought_qa' 

    Similar to thought, but variable output includes instruction. 
    This makes it useful for cases where we want to store a question and an answer in a variable
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)

    def get_variable_output(self,user_reply,memory_object):


        last_instruction  = memory_object.get_last_instruction()

        
        last_reply =memory_object.get_last_reply()

        variable_output = last_instruction+"\n\n"+last_reply




        return variable_output



class ThoughtExactNode(ThoughtNode):
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)

    """

    Corresponds to action = 'thought_exact' 

    Like the thought node, but output is forced instead of decided by model.
    Mostly useful for setting variables to fixed values. Slightly different from setting string with python_function node as it appends conversation turns.
    """

    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):

        instruction = set_variables(self.instruction,memory_object.get_variable_dict())

        response = instruction


        memory_object.append_state(self.name)



        turn_dict = {"retain_instruction":True,"user_reply":user_reply,"agent_reply":response,"instruction":"Reply with this exact text: " +instruction,"state":self.name,"category":self.state_category,"is_reply":False,"is_thought":True}
        memory_object.append_turn(**turn_dict)


        response_to_user=False

        #set for any node that consumes input
        new_user_reply=""

        return response,new_user_reply,response_to_user