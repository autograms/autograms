
import random

import numpy as np


import time



from ..autogram_config import LAST_RESPONSE_TOKEN,INSTRUCTION_TOKEN,AGENT_NAME_TOKEN

from ..autogram_utils import set_variables, predict_interjection_state, apply_classifier, apply_chatbot, apply_template, simulate_interjections, get_interjection_states


#allowable fields in spreadsheet (actual spreadsheets are case insensitive and can use spaces in place of "_"), matches with __init__ function to base node
EXPECTED_FIELDS = ['action','name','transitions','state_category','notes','transition_probs','instruction','instruction_short','user_instruction_transition_a','user_instruction_transition_b','user_instruction_transition_c','user_instruction_transition_d','user_instruction_transition_e','question_prompt','transition_question','transition_choice_a','transition_choice_b','transition_choice_c','transition_choice_d','transition_choice_e','user_interjection','condition_interjection','probability_interjection','example_interjection','prerequisite_states','blocking_states','up_weight_states','down_weight_states','boolean_condition','required_revisit','conv_scope','conv_context','transition_context','reply_start','instruction_template']

class BaseNode():
    """
    Class that defines node behaviors. Not meant to be instantiated, but all node types are derived from this class.
    Most node types override the apply_instruction() method in BaseNode, some override apply_transition() and get_variable_output(). 
    
    """

    def __init__(
            self,
            autogram_config,
            statement_interpreter=None,
            action=None,
            name=None,
            transitions=[],
            notes=None,
            state_category=None,
            transition_probs=[],
            instruction=None,
            instruction_short=None,
            user_instruction_transitions=[],
            question_prompt=None,
            transition_question=None,
            transition_choices=[],
            user_interjection=None,
            condition_interjection=None,
            probability_interjection=None,
            example_interjection=None,
            prerequisite_states=[],
            blocking_states=[],
            up_weight_states=[],
            down_weight_states=[],
            boolean_condition=None,
            required_revisit=[],
            conv_scope=None,
            conv_context=None,
            transition_context=None,
            reply_start=None,
            instruction_template=None
            ):
        
        """
        Initialize a new node
        args:
            autogram_config -- AutogramConfig object for autogram creating node, has many default settings for prompts
            statement_interpreter -- interpreter for python-style statements and functions that need to be interpreted by the node, used only by python function nodes as of initial version but may later be integrated more
            action -- type of action performed by node, also corresponds to node sub type
            name -- unique state name of node
            transitions -- list of allowable transitions
            notes -- comments about what the node does
            state_category -- user defined type of state. Names can be matched with `conv_scope` to view only states of that type when applying instruction
            transition_probs --list of floats used for simulation probabilities of each possible transition
            instruction -- instruction associated with node
            user_instruction_transitions -- list of user instruction for when user simulates each transition. Should be same length as transitions
            question_prompt -- prompt for transition question
            transition_question -- question asked to determine which state to transition to.
            transition_choices -- list of answers choices for transition question. If n'th transition choice is picked by model, autogram selects n'th transition. Should be same length as transitions
            user_interjection -- user instruction when simulating interjection. Only interjection states use this. See predict_interjection() function
            condition_interjection -- The answer to a multiple choice question used to predict an interjection. Only interjection states use this. See predict_interjection() function
            probability_interjection -- The probability of simulating an interjection to this state during simulation. Only interjection states use this.
            example_interjection -- Optional few shot example used to help predict interjection states.
            prerequisite_states -- list of states used for special .* transitions, when chosing between possible transitions, heavily downweight if these states are not in stored states in memory object
            blocking_states -- list of states used for special .* transitions, when chosing between possible transitions, heavily downweight if these states are in stored states in memory object
            up_weight_states -- list of states used for special .* transitions, when chosing between possible transitions, slightly upweight if these states are in stored states in memory object
            down_weight_states -- list of states used for special .* transitions, when chosing between possible transitions, slightly downweight if these states are in stored states in memory object. Can be used to penalize visiting the same state too often.
            boolean_condition -- either variable or python statement that is evaluated as boolean, used for .* transitions. If True, select this node, otherwise go to next node in .* list
            required_revisit -- list of states used to block function execution if states haven't been reached since last time function was called
            conv_scope -- only view states corresponding to user defined state types in state category. If used, conv_scope should match the state_category of some of the nodes
            transition_context --number of turns of context to use for transition prediction with classifier. Defaults to 1 if using default AutogramConfig
            instruction_template --template for how instruction and last reply are displayed to model. Default is "<last_reponse>\n\nInstruction for <agent_name>: <instruction>" if using default AutogramConfig        
        """

        """
        nodes that are callable by function nodes have naming convention  `node_name(arg1,arg2,...,argn)`
        these names are parsed, name is stored as `node_name()` and args are stored in seperate list
        nodes that are not callable by function nodes do not have any processing done to their name
        """
        if "(" in name:
            ind = name.find("(")
            ind2 = name.find(")")
            if ind2 < ind:
                raise Exception("invalid node name "+str(name))
            else:
                arg_str = name[ind+1:ind2]
                if len(arg_str)==0:
                    self.args=[]
                else:
                    self.args = arg_str.split(",")
                    self.args = [x.replace(" ","") for x in self.args]
                self.name = name[:ind] + "()"

        else:
            self.name  = name
            self.args=[]
        self.action = action
        self.statement_interpreter=statement_interpreter
    

        if notes is None:
            self.notes=""
        else:
            self.notes=notes

        if state_category is None:
            self.state_category=""
        else:
            self.state_category=state_category

        if instruction is None:
            self.instruction = ""
        else:
            self.instruction = instruction


        self.instruction_short = instruction_short


        if user_instruction_transitions is None:
            self.user_sims=[]
            
        else:
            self.user_sims=user_instruction_transitions


        if transitions is None:
            self.transitions = []
            
        else:
            self.transitions = transitions


            


        if transition_probs is None or len(transition_probs)==0:
            
            delta_p = autogram_config.default_primary_prob_detla
            if delta_p>1 or delta_p<0:
                Exception("invalid value for config parameter default_primary_prob_detla")

            """
            solves sytem of equations to set probability of first transition to be higher than all other transitions by autogram_config.default_primary_prob_detla (or 1 if there is 1 transition)
            A=P(default transtion), B=P(other transitions), n = number of possible transitions, d = default_primary_prob_detla
            A+(n-1)*B = 1
            A = d+B
            d+B+(n-1)*B = 1
            (n)*B = 1-d
            B = (1-d)/n
            A = d + (1-d)/n
            """
            if len(self.transitions)==0:
                import pdb;pdb.set_trace()
                
            
            self.transition_probs = np.array([(1-delta_p)/(len(self.transitions))]*len(self.transitions))
            self.transition_probs[0]+=delta_p




        else:
    
            self.transition_probs = np.array(transition_probs)
            if not(np.sum(self.transition_probs)):
                raise Exception("Transition probs for node "+str(self.name)+" must sum to 1.")


        if not question_prompt is None:
            self.question_prompt = question_prompt
        else:
            self.question_prompt=autogram_config.default_question_prompt

        if transition_choices is None:
            self.transition_answers=[]
            
        else:
            self.transition_answers=transition_choices
            
        if transition_question is None:
            self.transition_question=None
            self.question_prompt=None

        else:
            self.transition_question=transition_question


        if prerequisite_states is None:
            self.prerequisite_states=[]
            
        else:
            self.prerequisite_states=prerequisite_states 
            



        if blocking_states is None:
            self.blocking_states=[]
            
        else:
            self.blocking_states=blocking_states
            



        if up_weight_states is None:
            self.up_weight_states=[]
        else:
            self.up_weight_states=up_weight_states

        if down_weight_states is None:
            self.down_weight_states=[]
        else:
            self.down_weight_states=down_weight_states

        self.boolean_condition = boolean_condition


        if required_revisit is None:
            self.required_revisit=[]
        else:
            self.required_revisit=required_revisit


        self.conv_scope=conv_scope

        self.conv_context=conv_context

        if transition_context is None:

            self.transition_context=transition_context
        else:
            self.transition_context=autogram_config.default_transition_context

        self.agent_name = autogram_config.agent_name

        self.user_name = autogram_config.user_name

        self.instruction_name = autogram_config.instruction_name


        self.reply_start_type=autogram_config.reply_start_type
        if reply_start is None:

            self.reply_start= autogram_config.default_reply_start_template.replace(AGENT_NAME_TOKEN,self.agent_name)   
        else:
            self.reply_start=reply_start


        self.user_reply_start= autogram_config.default_reply_start_template.replace(AGENT_NAME_TOKEN,self.user_name) 


        if instruction_template is None:
            self.instruction_template=autogram_config.instruction_template

        else:
            self.instruction_template=instruction_template


        self.user_instruction_template = autogram_config.user_instruction_template


        if condition_interjection is None:
            self.condition_interjection=None
            self.probability_interjection=None
            self.user_interjection=None
            self.example_interjection=None



        else:
            self.condition_interjection=condition_interjection

            if probability_interjection is None:
                self.probability_interjection=float(autogram_config.default_probability_interjection)
            else:
                self.probability_interjection=float(probability_interjection)


            self.user_interjection=user_interjection
            self.example_interjection=example_interjection





        if len(self.user_sims)>0 and self.user_sims[0]==autogram_config.end_signal:
            self.terminal=True
        elif self.instruction=="quit":
            self.terminal=True
        else:
            self.terminal=False


    def predict_next_state(self,inputs,outputs,classifier,transition_question,memory_object):
        """
        args:

        Use classifier to predict a transition. For instance, the classifier might be asked a question like:

        Which of the following did the user do?
        A. The user responded affirmatively or with a yes.
        B. The user responded negatively or with a no.
        C. The user asked a question or seems confused.
         
        
        Depending on whether the model predicts A, B, or C, the graph will next go to the state defined in self.transitions[0], self.transitions[1], or self.transitions[2] respectively.
        
        args:
            inputs -- list of previous inputs given to model, see make_prompt() to better understand how these are defined
            outputs -- list of previous outputs from the model, see make_prompt() to better understand how these are defined
            classifier -- classifier model to predict multiple choice to determine transition
            transition_question -- Question asked to classifier model. post processed version of self.transition_question with variables set.
            memory_object -- MemoryObject that keeps track of conversation history and variables
        returns:
            new_node_id -- next state predicted based on model's answer

        """

        if len(self.transitions)==1:
            return self.transitions[0]

        answers = 1*self.transition_answers

        abcde = "ABCDE"[:len(answers)]

        content = self.question_prompt+"\n\n"
        if len(inputs)>0:


            
            for i in range(len(inputs)):
                if len(outputs)==len(inputs):
                
                    content +=outputs[i]+"\n\n"
                else:
                    if i>0:
                        content +=outputs[i-1]+"\n\n"

                content +=inputs[i]+"\n\n"


            



        content+=transition_question+"\n"
      



        if len(answers)==2 and (answers[0].lower()=="yes" or answers[1].lower()=="no") or (answers[1].lower()=="yes" or answers[0].lower()=="no"):
           
            """
            yes or no questions have special treatment. Model predicts yes or no token. This makes the ordering of yes and no arbitrary for the classifier.
            """
           
            content+=" (Yes or No)"

            if answers[0].lower()=="no":
                answers[0]="No"
                answers[1]="Yes"
            else:

                answers[0]="Yes"
                answers[1]="No"

            choices=answers


        else:

            """
            If not a yes or no question, model predicts multiple choice output token A, B, ... etc.
            """
           
            for i in range(len(answers)):
                content+=abcde[i] + ". " +  answers[i] +"\n"

            choices=abcde

        class_id,success=apply_classifier(classifier,content,choices=choices,memory_object=memory_object,state=self.name,transition_probs=self.transition_probs)  

        return self.transitions[class_id]
    

    def simulate_transition(self):

        """
        Used to simulate transitions during user reply simulations. Samples transition from transition probabilities
        returns:
            new_node_id -- name of next state
        """

        if len(self.transitions)==1:
            return self.transitions[0]
        else:
            id = np.random.choice(len(self.transitions),p=self.transition_probs)
            return self.transitions[id]

    def make_interjection_prompt(self,agent_replies,user_replies,start_prompt):
        """
        make prompt for user bot to simulate user during simulated interjection where agent breaks out of main graph
        args:
            agent_replies -- list of previous conversational replies from the agent
            user_replies --list of previous conversational replies from the user
            start_prompt --starting prompt for user bot
        returns:
            inputs -- previous inputs to chatbot model
            outputs -- previous outputs from chatbot model
            reply_prefix_text -- start of reply, only compatible with completion style and huggingface models, otherwise should be None
        """


        user_instruction = self.user_interjection
        inputs = [start_prompt+"\n\n"+self.agent_name+ agent_replies[0]]
        outputs = []

        for i in range(1,len(agent_replies)):
            outputs.append(user_replies[i-1])
            inputs.append(agent_replies[i])

        last_response_start = self.instruction_template.find(LAST_RESPONSE_TOKEN)
        if last_response_start<0:
            raise Exception("last response token "+LAST_RESPONSE_TOKEN+" is missing in instruction_template in config or state "+self.name)
        else:
            last_response_finish = last_response_start+len(LAST_RESPONSE_TOKEN)
        
        instruction_start = self.instruction_template.find(INSTRUCTION_TOKEN)
        if instruction_start<0:
            raise Exception("instruction token "+INSTRUCTION_TOKEN+" is missing in instruction_template in config or state "+self.nam)
        else:
            instruction_finish = instruction_start+len(INSTRUCTION_TOKEN)

        starts = [last_response_start,instruction_start]
        fins = [last_response_finish,instruction_finish]
        texts = [agent_replies[-1],user_instruction]

        last_turn = apply_template(starts,fins,texts,self.user_instruction_template)

        last_turn,reply_prefix_text= self.proc_reply_start(last_turn,self.user_reply_start)
        inputs[-1] =last_turn
        return inputs,outputs,reply_prefix_text



    def make_user_prompt(self,agent_replies,user_replies,start_prompt,next_state):
        """
        make prompt for user bot to simulate user. 
        args:
            agent_replies -- list of previous conversational replies from the agent
            user_replies --list of previous conversational replies from the user
            start_prompt --starting prompt for user bot
            next_state -- new state that was sampled to determine which user prompt to select
        returns:
            inputs -- previous inputs to chatbot model
            outputs -- previous outputs from chatbot model
            reply_prefix_text -- start of reply, only compatible with completion style and huggingface models, otherwise should be None
        """

        index = self.transitions.index(next_state)
        user_instruction = self.user_sims[index]


        inputs = [start_prompt+"\n\n"+self.agent_name+ agent_replies[0]]
        outputs = []


        for i in range(1,len(agent_replies)):
            outputs.append(user_replies[i-1])
            inputs.append(agent_replies[i])

            
        last_response_start = self.user_instruction_template.find(LAST_RESPONSE_TOKEN)
        if last_response_start<0:
            raise Exception("last response token "+LAST_RESPONSE_TOKEN+" is missing in instruction_template in config or state "+self.name)
        else:
            last_response_finish = last_response_start+len(LAST_RESPONSE_TOKEN)
        
        instruction_start = self.user_instruction_template.find(INSTRUCTION_TOKEN)
        if instruction_start<0:
            raise Exception("instruction token "+INSTRUCTION_TOKEN+" is missing in instruction_template in config or state "+self.nam)
        else:
            instruction_finish = instruction_start+len(INSTRUCTION_TOKEN)

        starts = [last_response_start,instruction_start]
        fins = [last_response_finish,instruction_finish]
        texts = [agent_replies[-1],user_instruction]

        last_turn = apply_template(starts,fins,texts,self.user_instruction_template)



        last_turn,reply_prefix_text = self.proc_reply_start(last_turn,self.user_reply_start)
        inputs[-1] =last_turn

        


    
        return inputs,outputs,reply_prefix_text
    

    
    def make_prompt(self,turns,start_prompt,nodes,required_category=None,max_turns=None,transition=False):
        """
        make prompt for chatbot
        args:
            turns -- list of previous conversation turns in memory object
            start_prompt -- prompt at beginning for autogram
            nodes -- all nodes in the autogram
            required_category -- only select replies in this category for prompt
            max_turns -- only show a maximum of max_turns in prompt
            transition -- whether or not this is a prompt for transition prediction

        returns:
            inputs -- previous inputs to chatbot model
            outputs -- previous outputs from chatbot model
            reply_prefix_text -- start of reply, only compatible with completion style and huggingface models, otherwise should be None
        """



        inputs=[]
        outputs=[]
        

        input_0 = start_prompt+"\n\n"

        

        for i in range(len(turns)-1):
            #iterates over past turns


            #check if this past turn is in category defined by required_category, usually defined by this turns conv_scope attribute
            if not (required_category is None) and len(required_category)>0:
                if not required_category == turns[i]["category"]:
                    continue

            
            retain_instruction = turns[i]["retain_instruction"]
            
            user_reply = turns[i]["user_reply"]
            instruction = turns[i]["instruction"]
            agent_reply = turns[i]["agent_reply"]
            node_id = turns[i]["state"]

            if len(agent_reply)>0:
                past_node = nodes[node_id]

                #calls node from previous turn to determine what text should go in input text for turn
                input_i = input_0+past_node.set_past_input(user_reply,retain_instruction,instruction,transition=transition)
                input_0=""
                inputs.append(input_i)

                #calls node from previous turn to determine what text should go in output text for that turn
                output_i = past_node.set_past_output(agent_reply,transition=transition)
                outputs.append(output_i)

        user_reply = turns[-1]["user_reply"]
        instruction = turns[-1]["instruction"]

        #get text in prompt for current turn
        input_i,reply_prefix_text = self.set_input(user_reply,instruction,transition=transition)

        input_i=input_0+input_i
        inputs.append(input_i)

        if not max_turns is None:
            inputs = inputs[-max_turns:]
            outputs = outputs[-max_turns:]

        


        return inputs,outputs,reply_prefix_text
    
    def proc_reply_start(self,last_turn,reply_start):
        """
        determines how to deal with the reply start, which will often be something like "Agent's reply:"
        Reply start can be set individually for each node. It is used as the start of the reply as an extra guide to the model to follow the instruction.
        Depends mainly on reply_start_type (Initialized from AutogramConfig), which can either be:
        "suffix" -- Append reply start to end of input. This is useful for chat style models that are behind an API, where we can't control the actual start of the reply
        "prefix" -- Start the reply with reply start, possible for completion models or locally running models.
        "none" -- don't use reply start

        args:
            last_turn -- text from last input
            reply_start -- reply start text (ex: Agent's reply:, Agent's answer to question:)
        returns:
            text -- new last turn after processing
            prefix -- start of next reply on decoder side, if any
        """
        if self.reply_start_type=='suffix':

            
            text =last_turn +"\n"+reply_start
            prefix=None
        elif self.reply_start_type=="prefix":
            text=last_turn
            prefix = reply_start
        else:
            text =last_turn
            prefix=None

        return text,prefix

    def set_past_input(self,user_reply,retain_instruction,instruction,transition):
        """
        Set text for previous turn for the model to see. 

        args:
            user_reply -- input text from user, or "" if this turn didn't involve interaction with user
            retain_instruction -- whether or not we should include the instruction from this past turn in the prompt for the current turn to see
            instruction -- processed instruction (with variables set) from the past turn
            transition -- whether or not this prompt is for transition prediction

        returns:
            text -- text the model will view for this past turn's input
        """
        if int(retain_instruction):
            #print("here")
            #text,_ = self.set_input(user_reply,instruction,transition)
            text,_ = self.set_input(user_reply,instruction,False)


        else:

            if not(user_reply) is None and len(user_reply)>0:
                text=self.user_name + ": "+user_reply

            else:
                text =""


            if self.reply_start_type=="suffix": # and not transition:
                text+="\n"+self.reply_start

        
        return text
    
    def set_past_output(self,agent_reply,transition):
        """
        Set text for previous turn for the model to see. 

        args:
            agent_reply -- text output by model at this past turn
            transition -- whether or not this prompt is for transition prediction

        returns:
            text -- text the model will view for this past turn's output
        """
   
        text = agent_reply
        #if self.reply_start_type=="prefix"  or transition:
        if self.reply_start_type=="prefix":
            text= self.reply_start+" "+text
        
        return text
    
    def set_input(self,user_reply,instruction,transition):
        """
        Set text for current turn

        args:
            user_reply -- input text from user, or "" if this turn didn't involve interaction with user
            instruction -- processed instruction (with variables set) from the past turn
            transition -- whether or not this prompt is for transition prediction

        returns:
            text -- text the model will view for this current turn's input, leftmost portion of prompt
        """




        if not(user_reply) is None and len(user_reply)>0:
            if self.reply_start_type=="none":
                last_reply = user_reply+ "\n\n"
            else:
                last_reply=self.user_name+": "+user_reply+ "\n\n"

        else:

            last_reply=""


        if transition:

            text = last_reply
            prefix=None

                
        else:  

            last_response_start = self.instruction_template.find(LAST_RESPONSE_TOKEN)
            if last_response_start<0:
                raise Exception("last response token "+LAST_RESPONSE_TOKEN+" is missing in instruction_template in config or state "+self.name)
            else:
                last_response_finish = last_response_start+len(LAST_RESPONSE_TOKEN)
            
            instruction_start = self.instruction_template.find(INSTRUCTION_TOKEN)
            if instruction_start<0:
                raise Exception("instruction token "+INSTRUCTION_TOKEN+" is missing in instruction_template in config or state "+self.nam)
            else:
                instruction_finish = instruction_start+len(INSTRUCTION_TOKEN)
            starts = [last_response_start,instruction_start]
            fins = [last_response_finish,instruction_finish]
            texts = [last_reply,instruction]


            agent_name_start = self.instruction_template.find(AGENT_NAME_TOKEN)
            if agent_name_start>0:
                starts.append(agent_name_start)
                fins.append(agent_name_start+len(AGENT_NAME_TOKEN))
                texts.append(self.agent_name)


            text= apply_template(starts,fins,texts,self.instruction_template)


            text,prefix = self.proc_reply_start(text,self.reply_start)



            

        return text, prefix

    
    def predict_interjection(self,memory_object,user_reply,classifier,nodes,autogram_config):
        """
        use classifier to predict whether we should apply an interjection, where autogram jumps from current point in graph to a predefined interjection state
        typically applies a multiple choice question such as:

        Which of the following is True?
        A. User wants xxx.
        B. User wants yyy.
        C. User wants zzz.
        D. None of the above.

        If the model predicts A, B, or C, this results in a jump to the state corresponding to that answer.
        If the model predicts the last option (None of the above.), things continue in the graph as normal

        args:
            user_reply -- input text from user, or "" if this turn didn't involve interaction with user
            instruction -- processed instruction (with variables set) from the past turn
            transition -- whether or not this prompt is for transition prediction

        returns:
            text -- text the model will view for this current turn's input, leftmost portion of prompt
        """
        if len(get_interjection_states(nodes))==0:
            return None

        if classifier.test_mode:
            pred_interjection=simulate_interjections(nodes,len(memory_object.get_agent_replies()),max_turns=1000)
        else:


            turns = memory_object.get_turns()
            start_prompt=""
            turns = memory_object.get_turns()
            input_turns =turns + [{"user_reply":user_reply, "instruction":""}]
            inputs,outputs,_ = self.make_prompt(input_turns,start_prompt,required_category=None,max_turns=1,transition=True,nodes=nodes)

            pred_interjection=predict_interjection_state(nodes, inputs,outputs, classifier=classifier,memory_object=memory_object,state=self.name,autogram_config=autogram_config)



        return pred_interjection

    
    #assign any variables that were retrieved
    def get_variable_output(self,user_reply,memory_obj):
        """
        Decides what the output to the variables that are assigned this turn should be. 
        This behavior may be different for different node types. 
        Most commonly will be the model's reply, but may also combine the instruction or the last user reply. 
        For function call nodes, it will be whatever was returned by that function
        For some other nodes, no variables are assigned and this will be the empty string

        args:
            user_reply -- user's previous reply
            memory_obj -- MemoryObject defining conversation history

        returns:
            variable_output -- variable set by this node

        
        """

        
        last_reply =memory_obj.get_last_reply()



        if last_reply is not None:
            variable_output=last_reply
        else:
            variable_output=None

        
        return variable_output

    #get next node id. This may include calling a function, or getting a return
    def apply_transition(self,user_reply,memory_object,classifier,nodes,autogram_config):
        """
        Decides which transiton to predict for the next state. 
        Behavior is sometimes different for different node types. For instance function nodes need to be able to transition to the node being called in the function.

        args:
            user_reply -- user's previous reply
            memory_object -- MemoryObject defining conversation history
            classifer -- model used to predict multiple choice answer
            nodes -- all nodes in autogram
            autogram_config -- AutogramConfig object with default autogram settings

        returns:
            new_node_id -- predicted transitions
        
        """
        if self.transition_question is None:
            transition_question=self.transition_question
        else:

            transition_question = set_variables(self.transition_question,memory_object.get_variable_dict(),is_inst=False)

        start_prompt=""
        turns = memory_object.get_turns()
        
        input_turns =turns + [{"user_reply":user_reply, "instruction":""}]



        inputs,outputs,_ = self.make_prompt(input_turns,start_prompt,required_category=None,max_turns=self.transition_context,transition=True,nodes=nodes)

        node_pred = self.predict_next_state(inputs,outputs,classifier,transition_question,memory_object)


        new_node_id=node_pred

  

        return new_node_id
    
    
    #apply instruction to get model response (or fixed response or null response)
    def apply_instruction(self,user_reply,memory_object,chatbot,nodes):
        """
        Executes instruction of node. Depending on node type, may involve call to the chatbot

        args:
            user_reply -- user's previous reply
            memory_object -- MemoryObject defining conversation history
            chatbot -- model used to generate text
            nodes -- all nodes in autogram

        returns:
            response -- model output of instruction
            new_user_reply -- what to set for user reply for next turn. Is usually either None (keep previous user reply) or "" (overwrite user reply with empty string). May allow more behaviors later.
            response_to_user -- are we giving this response to the user. Usually True for chat nodes, false for other node types
        """
        response=None
        response_to_user=False
        new_user_reply=None

        memory_object.append_state(self.name)
        turn_dict = {"retain_instruction":'0',"user_reply":"","agent_reply":"","instruction":"","state":self.name,"category":self.state_category,"is_reply":False}

        memory_object.append_turn(**turn_dict)
        return response,new_user_reply,response_to_user




























