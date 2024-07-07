from .base_node import BaseNode
from ..autogram_utils import apply_chatbot,set_variables,check_contains_variables

class ChatNode(BaseNode):
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)
        """
        Corresponds to action = 'chat' 
        Node to follow instruction to reply to user. Will break out of while loop defined in reply() function of Autogram class
        """

    def apply_transition(self,user_reply,memory_object,classifier,nodes,autogram_config):

        """
        Unlike in BaseNode, apply_transition for ChatNode can result in interjections if nodes with interjection conditions are defined
        Interjection nodes can be reached from any chat nodes if the user reply is predicted to meet the critera
        
        Note that apply_transition() will be applied after the chat node has executed it's instruction and replies to the user,
        so at this stage the autogram will have just recieved a new user reply
        
        """


        pred_interjection =self.predict_interjection(memory_object,user_reply,classifier,nodes,autogram_config)


        if pred_interjection is None:
            if self.transition_question is None:
                transition_question=self.transition_question
            else:

                transition_question = set_variables(self.transition_question,memory_object.get_variable_dict(),is_inst=False)
            turns = memory_object.get_thought_chat_turns()

            input_turns =turns + [{"user_reply":user_reply, "instruction":""}]

            inputs,outputs,_ = self.make_prompt(input_turns,start_prompt="",required_category=None,max_turns=self.transition_context,transition=True,nodes=nodes)

            node_pred = self.predict_next_state(inputs,outputs,classifier,transition_question,memory_object)

            new_node_id=node_pred
        else:
            new_node_id=pred_interjection


        return new_node_id

    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):

        instruction = set_variables(self.instruction,memory_object.get_variable_dict())


        """
        ChatNodes retain instruction in the prompt when either:
            - the previous user reply wasn't defined (for instance if a thought node was called before replying)
            - the instruction contains variables -- these could be useful to be viewed at future turns

        Otherwise, the instruction applied here becomes invisible to the model during later turns of the conversation to prevent prompt from getting too crowded
        """
        if len(user_reply)==0:
            retain_instruction=True
        else:
            retain_instruction = check_contains_variables(self.instruction,memory_object)


        required_text=""

        start_prompt=memory_object.get_prompt()
        turns = memory_object.get_thought_chat_turns()
        input_turns =turns + [{"user_reply":user_reply, "instruction":instruction}]

        inputs,outputs,prefix = self.make_prompt(input_turns,start_prompt,required_category=self.conv_scope,transition=False,nodes=nodes)


        response,success=apply_chatbot(chatbot,memory_object,inputs,outputs,prefix,required_text,self.name)


        memory_object.append_state(self.name)
        turn_dict = {"retain_instruction":retain_instruction,"user_reply":user_reply,"agent_reply":response,"instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":True}
        memory_object.append_turn(**turn_dict)


        response_to_user=True

        #set for any node that consumes input
        new_user_reply=""

        return response,new_user_reply,response_to_user
    


        

        

class ChatSuffixNode(ChatNode):
    """
    Corresponds to action = 'chat_suffix' 

    Similar to chat node, except that instruction has custom modifcation to try to force it to use instruction text at the end of the reply
     
    If using default AutogramConfig, instruction is modifed here to say:
    "Respond to the user's last reply, and then include the **bold** text at the end of your response to direct the conversation:**" + instruction +"**. It is also okay for the whole repsonse to be the bold text if it fits the situation."
    
    This also contains an autocompletion functionality that is useful if the instruction text is long, allowing model to complete text even if context window isn't long enough
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)

    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):

        instruction = set_variables(self.instruction,memory_object.get_variable_dict())

        if len(user_reply)==0:
            retain_instruction=True
        else:
            retain_instruction = check_contains_variables(self.instruction,memory_object)


        required_text=instruction

        instruction = "Respond to the user's last reply, and then include the **bold** text at the end of your response to direct the conversation:**" + instruction +"**. It is also okay for the whole repsonse to be the bold text if it fits the situation."

        start_prompt=memory_object.get_prompt()
        turns = memory_object.get_thought_chat_turns()
        input_turns =turns + [{"user_reply":user_reply,  "instruction":instruction}]

        inputs,outputs,prefix = self.make_prompt(input_turns,start_prompt,required_category=self.conv_scope,transition=False,nodes=nodes)


        response,success=apply_chatbot(chatbot,memory_object,inputs,outputs,prefix,required_text,self.name)



        memory_object.append_state(self.name)

        turn_dict = {"retain_instruction":retain_instruction,"user_reply":user_reply,"agent_reply":response,"instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":True}
        memory_object.append_turn(**turn_dict)


        response_to_user=True

        #set for any node that consumes input
        new_user_reply=""

        return response,new_user_reply,response_to_user


class ChatExactNode(ChatNode):
    """
    Corresponds to action = 'chat_exact' 

    Reply with exact text in instruction.
    """
    def __init__(self,autogram_config,statement_interpreter=None,**kwargs):
        super().__init__(autogram_config,statement_interpreter,**kwargs)

    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):



        instruction = set_variables(self.instruction,memory_object.get_variable_dict())

        retain_instruction = False 

        required_text=instruction


        response = instruction

        memory_object.append_state(self.name)

        instruction="Reply to the user with the following text **"+instruction +"**"

        turn_dict = {"retain_instruction":retain_instruction,"user_reply":user_reply,"agent_reply":response,"instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":True}
        memory_object.append_turn(**turn_dict)

      


        response_to_user=True

        #set for any node that consumes input
        new_user_reply=""

        return response,new_user_reply,response_to_user