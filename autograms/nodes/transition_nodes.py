from .base_node import BaseNode




class TransitionNode(BaseNode):
    """
    Action-less node that allows for an extra transition question. 
    Corresponds to action = "transition" 
    Allows for additional branching in the graph. Behavior is very similar to BaseNode.
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)



    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):
        response=None
        response_to_user=False
        new_user_reply=None
        memory_object.append_state(self.name)

        
        return response,new_user_reply,response_to_user