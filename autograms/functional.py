from .memory import get_memory
from .program_control import ReplyExit,GoTo,ReturnTo, FunctionExit
from . import apis
import numpy as np
from .autogram_utils.prompt_utils import make_prompt,make_decision_prompt
import random


from .autogram_utils.post_process_utils import process_node_id, post_process_responses

from pydantic import BaseModel, create_model




def reply(text):    
    """
    Sends a direct reply and logs it as a chat turn.

    Parameters:
    - text (str): The reply text to be sent.

    Raises:
    - ReplyExit: Exception to handle the reply in the program control flow.
    """
    exc=ReplyExit(text)
    log_chat_turn(text,line_number = exc.line_number,function_name = exc.function_name)
    raise exc

def reply_instruction(instruction):
    """
    Generates a reply based on the given instruction and logs it.

    Parameters:
    - instruction (str): Instruction guiding the chatbot response.

    Raises:
    - ReplyExit: Exception to handle the reply in the program control flow.
    """
    response= call_conv_model(instruction)

    reply(response)

def reply_suffix(instruction):
    """
    Appends specific text to a chatbot reply and logs it.

    Parameters:
    - instruction (str): Text to be appended as a suffix in the reply.

    Raises:
    - ReplyExit: Exception to handle the reply in the program control flow.
    """
    required_text=instruction

    instruction = "Respond to the user's last reply, and then include the **bold** text at the end of your response to direct the conversation:**" + instruction +"**. It is also okay for the whole repsonse to be the bold text if it fits the situation."

    result = call_conv_model(instruction)
    
    response,req_satisfied = post_process_responses([result],required_text)

    reply(response)



def TRANSITION(transition_question,transitions,max_turns=1,**kwargs):
    """
    Handles transitions between different conversation states based on user input.

    Parameters:
    - transition_question (str): The question prompting the user for a decision.
    - transitions (dict): Mapping of transition choices to node addresses.
    - max_turns (int): Maximum number of turns allowed to make a decision.
    - **kwargs: Additional arguments for the decision process.

    Raises:
    - GoTo: Exception for transitioning to the selected node.
    """

    transition_choices = list(transitions.keys())
    transition_ids = list(transitions.values())

    if len(transition_choices)==2 and (transition_choices[0].lower()=="yes" and transition_choices[1].lower()=="no" or transition_choices[1].lower()=="yes" and transition_choices[0].lower()=="no"): 
        decision = yes_or_no(question=transition_question,max_turns=max_turns,**kwargs)
        if (transition_choices[0].lower()=="yes")==decision:
            new_node_id=transition_ids[0]
        else:
            new_node_id=transition_ids[1]

    else:
        decision = multiple_choice(question=transition_question,choices=transition_choices,max_turns=max_turns,**kwargs)
        new_node_id=transition_ids[decision]

    transition_exc = process_node_id(new_node_id)

    raise transition_exc


def EXIT(data={}):
    """
    Exits the current function with data.
    
    Parameters:
    - data (dict): Data to return upon function exit.
    
    Raises:
    - FunctionExit: To exit the function and return data.
    """
    raise FunctionExit(data)

def GOTO(destination):
    """
    Jumps to a predefined address in the function.

    Parameters:
    - destination (str): The target address to jump to.

    Raises:
    - GoTo: To jump to the specified address.
    """
    raise GoTo(destination)

def RETURNTO(destination):
    """
    Returns to a predefined address earlier in the call stack.

    Parameters:
    - destination (str): The target address to return to.

    Raises:
    - ReturnTo: To return to the specified address.
    """
    raise ReturnTo(destination)



def silent_thought(instruction):
    """
    Executes a thought (internal reasoning) instruction without logging.

    Parameters:
    - instruction (str): Instruction guiding the thought process.

    Returns:
    - str: The generated response.
    """
    response=call_conv_model(instruction)

    return response

def thought(instruction):
    """
    Executes a thought (internal reasoning) instruction and logs the response.

    Parameters:
    - instruction (str): Instruction guiding the thought process.

    Returns:
    - str: The generated response.
    """
    response = call_conv_model(instruction)


    log_thought_turn(response,instruction)

    return response


def multiple_choice(question,choices,max_turns=1,**kwargs):
    """
    Presents a multiple-choice question to the agent and returns its selection, used for decision making

    Parameters:
    - question (str): The multiple-choice question.
    - choices (list of str): Available choices.
    - max_turns (int): Maximum number of turns for decision making.
    - **kwargs: Additional parameters for the classifier.

    Returns:
    - int: Index of the selected choice.
    """
    memory_object = get_memory()
    turns,system_prompt = memory_object.get_turns_for_model()
    content,choices = make_decision_prompt(turns,question,choices,max_turns)
    
    answer,success = call_classifier(content,choices,**kwargs)
    if success and answer in choices:
        return choices.index(answer)
    else:
        return 0


def yes_or_no(question,max_turns=1,**kwargs):

    """
    Asks a yes-or-no question to the agent and returns the agent's answer.

    Parameters:
    - question (str): The yes-or-no question.
    - max_turns (int): Maximum number of turns for decision making.
    - **kwargs: Additional parameters for the classifier.

    Returns:
    - bool: True for 'Yes', False otherwise.
    """
    memory_object = get_memory()
    turns,system_prompt = memory_object.get_turns_for_model()
    content,choices = make_decision_prompt(turns,question,answers=["Yes","No"],max_turns=max_turns)
    answer,success = call_classifier(content,choices,**kwargs)

    if success and answer in choices:
        if answer=="Yes":
            return True
    return False

def call_conv_model(instruction):
    """
    Calls the conversational model with the given instruction.

    Parameters:
    - instruction (str): Instruction for the model.

    Returns:
    - str: The model's response.
    """
    input_turns,output_turns,system_prompt = get_turn_history(instruction=instruction)
    memory_object = get_memory()
    if not memory_object.test_mode:
        result,success = call_model(input_turns,output_turns,system_prompt,system_prompt_in_turns=memory_object.config.system_prompt_in_turns)
        return result[0]
    else:
        return "test mode, no response enabled"


def call_classifier(input_str,answer_choices,model_type=None,model_path=None,**kwargs):
    """
    Calls a classifier model to determine the best choice from given options.

    Parameters:
    - input_str (str): Input prompt for the classifier.
    - answer_choices (list of str): List of possible answers.
    - model_type (str, optional): Type of model to use.
    - model_path (str, optional): Path to the model.
    - **kwargs: Additional parameters for the classifier.

    Returns:
    - tuple: (selected_answer, success_flag)
    """
    memory_object = get_memory()
    if not memory_object.test_mode:

        if model_type is None:
            model_type=memory_object.config.chatbot_type

        if model_type=='openai':
            func = apis.openai_models.call_openai_classifier
            preprocess_func =apis.openai_models.get_classifier_messages

        messages = preprocess_func(input_str,model=model_path)
        result,success = func(messages,answer_choices,**kwargs)
    else:
        result = random.choice(answer_choices)
        success=True


    memory_object.log_classifier_turn(result,input_str,answer_choices,model_type=model_type)

    return result,success

def get_batch_embedding(texts,model_type='openai'):
    """
    Gets embeddings for a batch of texts.

    Parameters:
    - texts (list of str): List of texts to embed.
    - model_type (str): Model type used for embedding.

    Returns:
    - list: Embeddings for the input texts.
    """
    if model_type=='openai':
        func = apis.openai_models.get_batch_embedding
    results = func(texts)
    return results

def get_single_embedding(text,model_type='openai'):
    """
    Gets embedding for a single text.

    Parameters:
    - text (str): The text to embed.
    - model_type (str): Model type used for embedding.

    Returns:
    - list: Embedding for the input text.
    """
    memory_object = get_memory()
    if memory_object.test_mode:
        result = np.random.randn(1536).tolist()

    else:
        if model_type=='openai':
            func = apis.openai_models.get_single_embedding
        result = func(text)

    return result

def call_model(input_turns,output_turns,system_prompt,system_prompt_in_turns=False,model_type=None,model_path=None,**kwargs):
    """
    Calls a conversational model and returns its response.

    Parameters:
    - input_turns (list): Input conversation history.
    - output_turns (list): Output conversation history.
    - system_prompt (str): System prompt for the model.
    - system_prompt_in_turns (bool): Whether to include system prompt in conversation turns.
    - model_type (str, optional): Type of model to use.
    - model_path (str, optional): Path to the model.
    - **kwargs: Additional parameters for the model.

    Returns:
    - tuple: (model response, success flag)
    """
    memory_object = get_memory()
    config = memory_object.config

    if model_type is None:
        model_type=memory_object.config.chatbot_type

    if model_type=='openai':
    
        func = apis.openai_models.call_openai_chatbot
 

        preprocess_func =apis.openai_models.get_chatbot_messages
        
    messages = preprocess_func(input_turns,output_turns,system_prompt,system_prompt_in_turns=system_prompt_in_turns,truncate_input=True,model=model_path)


    result,success = func(messages,model=model_path,**kwargs)


    memory_object.log_chatbot_turn(result,input_turns,output_turns,system_prompt,model_type=model_type)
    return result,success



def generate_list(instruction,**kwargs):
    """
    Generates a list based on the given instruction using a predefined list structure.

    Parameters:
    - instruction (str): The instruction for generating the list.
    - **kwargs: Additional arguments for model configuration.

    Returns:
    - list[str]: A list of generated items.
    """
    memory_object = get_memory()
    config = memory_object.config

    class SimpleList(BaseModel):
        items: list[str]


    result = generate_object(instruction,SimpleList,**kwargs)

    
    return result.items
def generate_fixed_list(instruction,num_items,**kwargs):
    """
    Generates a list of a fixed number of items based on the given instruction.

    Parameters:
    - instruction (str): The instruction for generating the list.
    - num_items (int): The fixed number of items in the list.
    - **kwargs: Additional arguments for model configuration.

    Returns:
    - list[str]: A list containing the generated items.
    """
    fields = {f'item{i}': (str, ...) for i in range(1, num_items + 1)}
    obj_structure=create_model('Items', **fields)
    result = generate_object(instruction,obj_structure,**kwargs)
    output_list = ["<No item available due to error>"]*num_items
   
    for i in range(1,num_items+1):

        try:
            output_list[i-1]=getattr(result,f"item{i}")
        except:
            break
    return output_list

def generate_fixed_dict(instruction, keys, **kwargs):
    """
    Generates a dictionary with fixed keys based on the given instruction.

    Parameters:
    - instruction (str): The instruction for generating the dictionary.
    - keys (list[str]): The fixed set of keys for the dictionary.
    - **kwargs: Additional arguments for model configuration.

    Returns:
    - dict: A dictionary with the generated values for each key.
    """
    # Dynamically create fields for the Pydantic model
    fields = {key: (str, ...) for key in keys}
    obj_structure = create_model('DynamicDictModel', **fields)

    # Generate object using your existing function
    try:
        result = generate_object(instruction, obj_structure, **kwargs)
    except Exception:
        # Fallback in case the generation fails
        return {key: "<No value available due to error>" for key in keys}

    # Extract values from the result and handle errors gracefully
    output_dict = {}
    for key in keys:
        try:
            output_dict[key] = getattr(result, key)
        except AttributeError:
            output_dict[key] = "<No value available due to error>"

    return output_dict


def generate_object(instruction,obj_structure,**kwargs):
    """
    Generates an object based on the given instruction and the provided structure.

    Parameters:
    - instruction (str): The instruction for generating the object.
    - obj_structure (BaseModel): The structure of the object to be generated.
    - **kwargs: Additional arguments for model configuration.

    Returns:
    - obj_structure: An instance of the specified object structure with generated values.
    """
    input_turns,output_turns,system_prompt = get_turn_history(instruction=instruction)
    memory_object = get_memory()
    if not memory_object.test_mode:
        result= call_object_model(input_turns,output_turns,system_prompt,system_prompt_in_turns=memory_object.config.system_prompt_in_turns,obj_structure=obj_structure,**kwargs)
        return result
    else:
        return initialize_with_defaults(obj_structure)
    
def call_object_model(input_turns,output_turns,system_prompt,system_prompt_in_turns=False,model_type=None,model_path=None,obj_structure=None,**kwargs):
    """
    Calls a model to generate an object formatted response.

    Parameters:
    - input_turns (list): Input conversation history.
    - output_turns (list): Output conversation history.
    - system_prompt (str): System prompt to guide the model.
    - system_prompt_in_turns (bool): Whether to include the system prompt in conversation turns.
    - model_type (str, optional): Type of model to use.
    - model_path (str, optional): Path to the model.
    - obj_structure (BaseModel): Structure for the expected response.
    - **kwargs: Additional parameters for the model.

    Returns:
    - obj_structure: An instance of the specified object structure with generated values.
    """
    memory_object = get_memory()
    config = memory_object.config

    if model_type is None:
        model_type=memory_object.config.chatbot_type

    if model_type=='openai':

        func = apis.openai_models.call_openai_chat_formatted

        preprocess_func =apis.openai_models.get_chatbot_messages
        
    messages = preprocess_func(input_turns,output_turns,system_prompt,system_prompt_in_turns=system_prompt_in_turns,truncate_input=True,model=model_path)

    
    result,raw_str,success = func(messages,model=model_path,obj_structure = obj_structure,**kwargs)
    
    if not success:
        result = initialize_with_defaults(obj_structure)
    else:
        memory_object.log_chatbot_turn(raw_str,input_turns,output_turns,system_prompt,model_type=model_type)
    return result

# Utility function to generate a default instance
def initialize_with_defaults(model_class):
    """
    Initializes an instance of a Pydantic model with default values for all fields.

    Parameters:
    - model_class (BaseModel): The model class to instantiate.

    Returns:
    - BaseModel: An instance of the model class with default values.
    """
    defaults = {}
    for field_name, field in model_class.__fields__.items():
        # Set default value based on the type
        if field.outer_type_ == str:
            defaults[field_name] = "<There was an error generating this message, please ignore>"
        elif field.outer_type_ == int:
            defaults[field_name] = 0
        elif field.outer_type_ == float:
            defaults[field_name] = 0.0
        elif field.outer_type_ == bool:
            defaults[field_name] = False
        elif hasattr(field.outer_type_, "__origin__") and field.outer_type_.__origin__ == list:
            defaults[field_name] = []
        elif issubclass(field.outer_type_, BaseModel):
            # Recursively initialize nested models
            defaults[field_name] = initialize_with_defaults(field.outer_type_)
        else:
            defaults[field_name] = None  # Use None for any other type

    return model_class.construct(**defaults)


def set_system_prompt(text):
    """
    Sets the system prompt for the current memory object.

    Parameters:
    - text (str): The system prompt text.
    """
    memory_object = get_memory()
    memory_object.set_system_prompt(text)


    
def get_turn_history(instruction="",max_turns=-1,conv_only=False):
    """
    Retrieves the conversation history, formatted for the model.

    Parameters:
    - instruction (str): Instruction for the current turn.
    - max_turns (int): Maximum number of turns to include in the history.
    - conv_only (bool): Whether to include only conversation-related turns.

    Returns:
    - tuple: (input_turns, output_turns, system_prompt)
    """

    memory_object = get_memory()
    turns,system_prompt = memory_object.get_turns_for_model(instruction)

    inputs,outputs,_= make_prompt(turns,max_turns=max_turns,transition=False)
   

    return inputs,outputs,system_prompt


def log_chat_turn(reply,instruction=None,line_number=None,function_name=None):
    """
    Logs a chat turn in the memory object.

    Parameters:
    - reply (str): The reply text.
    - instruction (str, optional): Instruction guiding the reply.
    - line_number (int, optional): Line number of the calling function.
    - function_name (str, optional): Name of the calling function.
    """
    memory_object = get_memory()
    memory_object.log_chat_turn(reply,instruction,line_number=line_number,function_name=function_name)

    


def log_thought_turn(reply,instruction):
    """
    Logs a thought turn in the memory object.

    Parameters:
    - reply (str): The response text for the thought.
    - instruction (str): Instruction guiding the thought.
    """
    memory_object = get_memory()
    memory_object.log_thought_turn(reply,instruction)






