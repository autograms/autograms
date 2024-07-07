from .base_node import BaseNode
from ..autogram_utils import set_variables

class PromptModifierNode(BaseNode):
    """
    Nodes that modify the  or user prompt. Not instantiated.
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)



class SetUserPromptNode(PromptModifierNode):
    """
    corresponds to action = "set_user_prompt" 
    sets the user prompt at the current scope
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)


    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):

        instruction = set_variables(self.instruction,memory_object.get_variable_dict())


        memory_object.set_user_prompt(instruction)

        turn_dict = {"retain_instruction":False,"user_reply":"","agent_reply":"","instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":False}


        memory_object.append_state(self.name)
        memory_object.append_turn(**turn_dict)

        response = None
        response_to_user=False
        new_user_reply=None

        return response,new_user_reply,response_to_user

class SetPromptNode(PromptModifierNode):
    """
    corresponds to action = "set_prompt" 
    sets the prompt at the current scope
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)

    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):

        instruction = set_variables(self.instruction,memory_object.get_variable_dict())


        memory_object.set_prompt(instruction)
        turn_dict = {"retain_instruction":False,"user_reply":"","agent_reply":"","instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":False}


        memory_object.append_state(self.name)
        memory_object.append_turn(**turn_dict)

        response = None
        response_to_user=False
        new_user_reply=None

        return response,new_user_reply,response_to_user

class AppendUserPromptNode(PromptModifierNode):
    """
    corresponds to action = "append_user_prompt" 
    appends the user prompt at the current scope
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)

    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):

        instruction = set_variables(self.instruction,memory_object.get_variable_dict())


        memory_object.set_user_prompt(instruction)
        turn_dict = {"retain_instruction":False,"user_reply":"","agent_reply":"","instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":False}


        memory_object.append_state(self.name)
        memory_object.append_turn(**turn_dict)

        response = None
        response_to_user=False
        new_user_reply=None

        return response,new_user_reply,response_to_user


class AppendPromptNode(PromptModifierNode):
    """
    corresponds to action = "append_prompt" 
    appends the prompt at the current scope
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)

    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):

        instruction = set_variables(self.instruction,memory_object.get_variable_dict())


        memory_object.append_prompt(instruction)
        turn_dict = {"retain_instruction":False,"user_reply":"","agent_reply":"","instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":False}


        memory_object.append_state(self.name)
        memory_object.append_turn(**turn_dict)

        response = None
        response_to_user=False
        new_user_reply=None

        return response,new_user_reply,response_to_user