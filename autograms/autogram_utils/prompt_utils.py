from ..autogram_config import LAST_RESPONSE_TOKEN,INSTRUCTION_TOKEN,AGENT_NAME_TOKEN
from ..memory import get_memory


# def set_prompt_config(autograms_config):
#     global config
#     config = autograms_config

def set_past_input(user_reply,retain_instruction,instruction,transition):
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
    config = get_memory().config
    if int(retain_instruction):
        #print("here")

        text,_ = set_input(user_reply,instruction,False)


    else:

        if not(user_reply) is None and len(user_reply)>0:
            text=config.user_name + ": "+user_reply

        else:
            text =""


        if config.reply_start_type=="suffix": # and not transition:
            text+="\n"+config.reply_start

    
    return text

def set_past_output(agent_reply,transition):
    """
    Set text for previous turn for the model to see. 

    args:
        agent_reply -- text output by model at this past turn
        transition -- whether or not this prompt is for transition prediction

    returns:
        text -- text the model will view for this past turn's output
    """
    config = get_memory().config

    text = agent_reply
    if transition:
        text=config.agent_name+": "+text

  
    if config.reply_start_type=="prefix":
        text= config.reply_start+" "+text
    
    return text



def set_input(user_reply,instruction,transition):
    """
    Set text for current turn

    args:
        user_reply -- input text from user, or "" if this turn didn't involve interaction with user
        instruction -- processed instruction (with variables set) from the past turn
        transition -- whether or not this prompt is for transition prediction

    returns:
        text -- text the model will view for this current turn's input, leftmost portion of prompt
    """
    config = get_memory().config




    if not(user_reply) is None and len(user_reply)>0:
        if config.reply_start_type=="none" and not transition:
            last_reply = user_reply+ "\n\n"
        else:
            last_reply=config.user_name+": "+user_reply+ "\n\n"

    else:

        last_reply=""


    if transition:

        text = last_reply
        prefix=None

            
    else:  

        last_response_start = config.instruction_template.find(LAST_RESPONSE_TOKEN)
        if last_response_start<0:
            raise Exception("last response token "+LAST_RESPONSE_TOKEN+" is missing in instruction_template in config or node.")
        else:
            last_response_finish = last_response_start+len(LAST_RESPONSE_TOKEN)
        
        instruction_start = config.instruction_template.find(INSTRUCTION_TOKEN)
        if instruction_start<0:
            raise Exception("instruction token "+INSTRUCTION_TOKEN+" is missing in instruction_template in config or node.")
        else:
            instruction_finish = instruction_start+len(INSTRUCTION_TOKEN)
        starts = [last_response_start,instruction_start]
        fins = [last_response_finish,instruction_finish]
        texts = [last_reply,instruction]


        agent_name_start = config.instruction_template.find(AGENT_NAME_TOKEN)
        if agent_name_start>0:
            starts.append(agent_name_start)
            fins.append(agent_name_start+len(AGENT_NAME_TOKEN))
            texts.append(config.agent_name)


        text= apply_template(starts,fins,texts,config.instruction_template)


        text,prefix = proc_reply_start(text,config.reply_start)



        

    return text, prefix

def make_prompt_old(turns,max_turns=None,transition=False):
    """
    process prompt for chatbot
    arguments:
        turns--list of turns from the memory object
        max_turns--max number of turn pairs to include in the prompts

    returns:
        inputs -- previous inputs to chatbot model
        outputs -- previous outputs from chatbot model
        reply_prefix_text (deprecated but may readd later) -- start of reply, only compatible with completion style models, otherwise should be None
    """



    inputs=[]
    outputs=[]
    

    input_0 = ""

    

    for i in range(len(turns)-1):
        #iterates over past turns


        retain_instruction = turns[i]["retain_instruction"]
        instruction= turns[i]["instruction"]
        user_reply= turns[i]["user_reply"]
        agent_reply = turns[i]["agent_reply"]
        



        if len(agent_reply)>0:
            # past_node = nodes[node_id]

            #calls node from previous turn to determine what text should go in input text for turn
            input_i = input_0+set_past_input(user_reply,retain_instruction,instruction,transition=transition)
            if len(input_i)==0:
                input_i="[No user reply here, agent replies next]"

            inputs.append(input_i)

            #calls node from previous turn to determine what text should go in output text for that turn
            output_i = set_past_output(agent_reply,transition=transition)
            outputs.append(output_i)

    user_reply = turns[-1]["user_reply"]
    instruction = turns[-1]["instruction"]

    #get text in prompt for current turn
    input_i,reply_prefix_text = set_input(user_reply,instruction,transition=transition)

    input_i=input_0+input_i
    inputs.append(input_i)

    import pdb;pdb.set_trace()

    if not max_turns is None and max_turns>0:
        inputs = inputs[-max_turns:]
        outputs = outputs[-max_turns:]

    

    
    return inputs,outputs,reply_prefix_text


def make_prompt_single(turns,instruction=None,max_turns=None,transition=False):


    if not max_turns is None:

        user_replies_found = 0
        min_index = 0
        for i in reversed(range(len(turns))):
            if turns[i]['role']=="user":
                user_replies_found +=1
            if turns[i]['role']=="agent" and user_replies_found==max_turns:
                min_index =i
        turns=turns[min_index:]


    if not transition:
        message = "The information below may contain replies given by the user,  replies given by you (the agent), instructions given by the system to you for internal reasoning, and answers to those system instructions given by you the agent. Be sure to consider the entire conversation history, paying special attention to the user and agent replies.\n\n"
    else:
        message =  "The information below may contain replies given by the agent, instructions given by the system to the agent for internal reasoning, and answers to those system instructions given by the agent. You will need to answer a question based on this information.\n\n"
    for turn in turns:
        #iterates over past turns
        if turn['role']=="user":
            message+="User: " +  turn['content']+"\n\n"
        if turn['role']=="agent":
            message+="Agent: " +  turn['content']+"\n\n"

        if turn['role']=="system_instruction":
            message+="System Instruction: " +  turn['content']+"\n\n"

        if turn['role']=="system_answer":
            message+="Agent Answer: " +  turn['content']+"\n\n"


        
        
    if not instruction is None:
        message+=f"\n\nFollow the instruction in **bold** for your next reply: **{instruction}**"
    return message


def make_prompt(turns,instruction=None,max_turns=None,transition=False):


    if not max_turns is None:

        user_replies_found = 0
        min_index = 0
        for i in reversed(range(len(turns))):
            if turns[i]['role']=="user":
                user_replies_found +=1
            if turns[i]['role']=="agent" and user_replies_found==max_turns:
                min_index =i
        turns=turns[min_index:]



    
    input_turns = []
    output_turns = []
    user_turn = False
    user_sub_messages = []
    system_sub_messages = []
    for turn in turns:
        #iterates over past turns

   
        if turn['role']=="agent":
            input_message =""
            if len(system_sub_messages)+len(user_sub_messages)==0:

                input_message="INSTRUCTION: Reply to the user."
            else:
                if len(system_sub_messages)>1:
                    

                    for turn in system_sub_messages:
                        if turn['role']=="system_instruction":
                            input_turns.append(f"Instruction: {turn['content']}")
                        if turn['role']=="system_answer":
                            output_turns.append(turn['content'])
                
                input_message=""

                for message in user_sub_messages:
                    input_message+="User: "+ message['content']
                    input_message+="\n\nINSTRUCTION: Reply to the user."

            input_turns.append(input_message)
            output_turns.append(turn['content'])
            user_sub_messages = []
            system_sub_messages = []
        elif turn['role']=="user":
            user_sub_messages.append(turn)
        else:
            system_sub_messages.append(turn)



    if len(system_sub_messages)>1:
        

        for turn in system_sub_messages:
            if turn['role']=="system_instruction":
                input_turns.append(f"INSTRUCTION: {turn['content']}")
            if turn['role']=="system_answer":
                output_turns.append(turn['content'])
    
    input_message=""

    for message in user_sub_messages:
        input_message+="User: "+ message['content']
    if transition:
        input_message+=f"\n\nQUESTION: {instruction}"
    else:
        input_message+=f"\n\nINSTRUCTION: {instruction}"

    input_turns.append(input_message)
    



    return input_turns,output_turns










def make_decision_prompt(turns,transition_question,answers,max_turns):
    """
    Prompt creation for multiple choice and yes or no style questions used for decision making

    arguments:
        turns--list of turns from the memory object
        transition_question -- question we are asking model
        answers -- possible answers to transition_question
        max_turns--max number of turn pairs to include in the prompts

    returns:
        content -- input string to model
        choices -- possible outputs of the model. should each map to a single token in the models tokenization

    """




    abcde = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:len(answers)]



    

    content=transition_question+"\n\n"
    



    if len(answers)==2 and ((answers[0].lower()=="yes" or answers[1].lower()=="no") or (answers[1].lower()=="yes" or answers[0].lower()=="no")):
        
        """
        yes or no questions have special treatment. Model predicts yes or no token. This makes the ordering of yes and no arbitrary for the classifier.
        """
        
        content+=" (Yes or No)?"

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

        choices=list(abcde)

    if  len(turns)>0 and not(max_turns==0):
        input_turns,output_turns = make_prompt(turns,instruction=content,max_turns=max_turns,transition = True)
    else:
        input_turns=["INSTRUCTION: "+content]
        output_turns=[]


    

  #  class_id,success=apply_classifier(classifier,content,choices=choices,memory_object=memory_object,state=node_name,transition_probs=transition_probs)  
 
    return input_turns,output_turns,choices


def apply_template(starts,fins,texts,instruction_template):

    
    grouped = list(zip(starts,fins,texts))
    grouped = sorted(grouped)

    for elem in reversed(grouped):
        start,fin,text = elem
        instruction_template = instruction_template[:start]+text+instruction_template[fin:]




    return instruction_template


def proc_reply_start(last_turn,reply_start):
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
    config = get_memory().config
    if config.reply_start_type=='suffix':

        
        text =last_turn +"\n"+reply_start
        prefix=None
    elif config.reply_start_type=="prefix":
        text=last_turn
        prefix = reply_start
    else:
        text =last_turn
        prefix=None

    return text,prefix