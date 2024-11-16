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
        if config.reply_start_type=="none":
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

def make_prompt(turns,max_turns=None,transition=False):
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
                input_i="[No reply here, ignore]"

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

    if not max_turns is None and max_turns>0:
        inputs = inputs[-max_turns:]
        outputs = outputs[-max_turns:]

    


    return inputs,outputs,reply_prefix_text
    

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

    inputs,outputs,_ = make_prompt(turns,max_turns=max_turns,transition=True)

    if len(answers)==0:
        return answers[0]


    abcde = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:len(answers)]

    content ="\n\n"
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

  #  class_id,success=apply_classifier(classifier,content,choices=choices,memory_object=memory_object,state=node_name,transition_probs=transition_probs)  
 
    return content,choices


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