from .memory import get_memory, set_memory, SimpleMemory
from .program_control import ReplyExit,GoTo,ReturnTo, FunctionExit,find_decorated_frame
from . import apis
import numpy as np
from .autogram_utils.prompt_utils import make_prompt,make_decision_prompt
import random
import copy


from .autogram_utils.post_process_utils import process_node_id, post_process_responses

from pydantic import BaseModel, create_model, Field, ValidationError, root_validator
from enum import Enum
from typing import Dict, Type, Literal, List
import json
import os
import subprocess
import tempfile
import re
import dill

from .program_control import AutogramsReturn
from .supervisors import supervisable


from concurrent.futures import ProcessPoolExecutor

import subprocess
import tempfile
import os


def reply(text,data=None,ADDRESS=None):    
    """
    Sends a direct reply and logs it as a chat turn.

    Parameters:
    - text (str): The reply text to be sent.
    - data (dict): optional data to be sent back in autograms return object sent by autogram.apply()
    - ADDRESS(str): Only used by compiler--used to recover position of function call in the code of an @autograms_function. Optional, useful mainly for changing the code while the memory is active, allowing line numbers to be mapped 

    Raises:
    - ReplyExit: Exception to handle the reply in the program control flow.
    """
    exc=ReplyExit(text,data=data,ADDRESS=ADDRESS)
    log_chat_turn(text,line_number = exc.line_number,function_name = exc.function_name)
    raise exc

@supervisable(function_type="reply")
def reply_instruction(instruction,data=None,ADDRESS=None,**kwargs):
    """
    Generates a reply based on the given instruction and logs it.

    Parameters:
    - instruction (str): Instruction guiding the chatbot response.
    - data (dict): optional data to be sent back in autograms return object sent by autogram.apply()
    - ADDRESS(str): Only used by compiler--used to recover position of function call in the code of an @autograms_function. Optional, useful mainly for changing the code while the memory is active, allowing line numbers to be mapped 
    Raises:
    - ReplyExit: Exception to handle the reply in the program control flow.
    """

    response= call_conv_model(instruction,**kwargs)

    reply(response,data=data,ADDRESS=ADDRESS)

@supervisable(function_type="reply")
def reply_suffix(instruction,data=None,ADDRESS=None):
    """
    Appends specific text to a chatbot reply and logs it.

    Parameters:
    - instruction (str): Text to be appended as a suffix in the reply.
    - data (dict): optional data to be sent back in autograms return object sent by autogram.apply()
    - ADDRESS(str): Only used by compiler--used to recover position of function call in the code of an @autograms_function. Optional, useful mainly for changing the code while the memory is active, allowing line numbers to be mapped 
    Raises:
    - ReplyExit: Exception to handle the reply in the program control flow.
    """
    required_text=instruction

    instruction = "Respond to the user's last reply, and then include the **bold** text at the end of your response to direct the conversation:**" + instruction +"**. It is also okay for the whole repsonse to be the bold text if it fits the situation."

    result = call_conv_model(instruction)
    
    response,req_satisfied = post_process_responses([result],required_text)

    reply(response,data=data,ADDRESS=ADDRESS)



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


def EXIT(data=None):
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


def local_thought(instruction,system_prompt="",**kwargs):

    memory_object = get_memory()
    config = memory_object.config
    input_turns = [instruction]
    output_turns=[]

    if not memory_object.test_mode:
        result,success = call_model(input_turns,output_turns,system_prompt,system_prompt_in_turns=memory_object.config.system_prompt_in_turns,**kwargs)
        return result[0]
    else:
        return "test mode, no response enabled"



@supervisable(function_type='generation')
def silent_thought(instruction,**kwargs):
    """
    Executes a thought (internal reasoning) instruction without logging.

    Parameters:
    - instruction (str): Instruction guiding the thought process.

    Returns:
    - str: The generated response.
    """
    response=call_conv_model(instruction,**kwargs)

    return response

@supervisable(function_type='generation')
def thought(instruction,**kwargs):
    """
    Executes a thought (internal reasoning) instruction and logs the response.

    Parameters:
    - instruction (str): Instruction guiding the thought process.

    Returns:
    - str: The generated response.
    """
    response = call_conv_model(instruction,**kwargs)


    log_thought_turn(response,instruction)

    return response


def multiple_choice_logits(question,choices,max_turns=1,**kwargs):
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

    if len(choices)>26:
        raise Exception("To many choices for multiple choice, maximum is 26")

    if not memory_object.config.classifier_mode=="logit":
        raise Exception(f"multiple_choice_logits not allowed for classifier mode: {memory_object.config.classifier_mode}, must set classifier mode to logit for this.") 
    turns,system_prompt = memory_object.get_turns_for_model()
    if memory_object.config.exclude_classifier_system_prompt:
        system_prompt=None


    input_turns,output_turns,choices = make_decision_prompt(turns,question,choices,max_turns)
    
    
    logits,success = call_classifier(input_turns,output_turns,choices,return_logits = True,system_prompt=system_prompt,**kwargs)
    return logits


    

@supervisable(function_type='selection')
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
    if len(choices)>26:
        raise Exception("To many choices for multiple choice, maximum is 26")
    memory_object = get_memory()
    turns,system_prompt = memory_object.get_turns_for_model()

    input_turns,output_turns,choices = make_decision_prompt(turns,question,choices,max_turns)

    if memory_object.config.classifier_type=="json":
        input_turns[-1]+= " (Respond as a json with format {\"answer\":answer})"

    if len(choices)==1:
        return 0
    
    if memory_object.config.exclude_classifier_system_prompt:
        system_prompt=None
    answer,success = call_classifier(input_turns,output_turns,choices,system_prompt=system_prompt,**kwargs)


    if not(type(answer)==str):
        answer=answer["answer"]
    
    if success and answer in choices:
        return choices.index(answer)
    else:
        return 0

@supervisable(function_type='binary')
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
    input_turns,output_turns,choices = make_decision_prompt(turns,question,answers=["Yes","No"],max_turns=max_turns)
    if memory_object.config.exclude_classifier_system_prompt:
        system_prompt=None
    answer,success = call_classifier(input_turns,output_turns,choices,system_prompt=system_prompt,**kwargs)


    if success and answer in choices:
        
        if answer=="Yes":
            return True
    return False

def call_conv_model(instruction,**kwargs):
    """
    Calls the conversational model with the given instruction.

    Parameters:
    - instruction (str): Instruction for the model.

    Returns:
    - str: The model's response.
    """
    if "max_turns" in kwargs:
        max_turns = kwargs['max_turns']
        del kwargs['max_turns']
    else:
        max_turns = None
    input_turns,output_turns,system_prompt = get_turn_history(instruction=instruction,max_turns=max_turns)
    memory_object = get_memory()
    # if "_forced_output" in kwargs:
    #     return  kwargs["_forced_output"]
        
    if not memory_object.test_mode:
        result,success = call_model(input_turns,output_turns,system_prompt,system_prompt_in_turns=memory_object.config.system_prompt_in_turns,**kwargs)
        return result
    else:
        return "test mode, no response enabled"


def call_classifier(input_turns,output_turns,answer_choices,system_prompt=None,model_type=None,model=None,multi_modal_inputs=None,**kwargs):
    """
    Calls a classifier model to determine the best choice from given options.

    Parameters:
    - input_str (str): Input prompt for the classifier.
    - answer_choices (list of str): List of possible answers.
    - model_type (str, optional): Type of model to use.
    - model (str, optional): Path to the model.
    - multi_modal_inputs - list[dict] --list of open ai style image or audio inputs for the model, for example :
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"}
                    } 
    - **kwargs: Additional parameters for the classifier.

    Returns:
    - tuple: (selected_answer, success_flag)
    """

    memory_object = get_memory()

    if model_type is None:
        model_type=memory_object.config.chatbot_type

    #if model_type=='openai':
    func = apis.openai_models.call_openai_classifier
    preprocess_func =apis.openai_models.get_classifier_messages


    if not memory_object.config.classifier_mode=="logit" and "class_biases" in kwargs and not kwargs["class_biases"] is None:
        raise Exception(f"class_biases not allowed for classifier_mode: {memory_object.config.classifier_mode},must set classifier mode to logit for this.")
  
    

    function_name = "call_classifier"
    function_inputs = {"input_turns":input_turns,"output_turns":output_turns,"answer_choices":answer_choices,"system_prompt":system_prompt,"multi_modal_inputs":multi_modal_inputs}
    
    messages = preprocess_func(input_turns,output_turns,system_prompt=system_prompt,system_prompt_in_turns=memory_object.config.system_prompt_in_turns,model=model,multi_modal_inputs=multi_modal_inputs)
    if "_forced_output" in kwargs:
        result = kwargs["_forced_output"]
        raw_result = kwargs["_forced_output"]
        supervisor_info = kwargs["_supervisor_info"]

        success=True
    else:
        supervisor_info=None
        if memory_object.config.classifier_mode=="logit":

            result,usage_log = func(messages,answer_choices,**kwargs)
            raw_result = result
        else:
            
          
            
            schema = make_decision_schema_json(answer_choices)
            if memory_object.config.classifier_type=="huggingface_tgi":

                schema = convert_openai_json_schema(schema)
            
            memory_object = get_memory()



            

            if not memory_object.test_mode:
                func = apis.openai_models.call_openai_chat_formatted
                kwargs['temperature']=0
                raw_result,_,usage_log = func(messages,model=model,obj_structure = schema,**kwargs)
                success = not(raw_result is None)
                try:
                    result_dict = json.loads(raw_result)
                    result = result_dict["answer"]
                except:
                    success=False

                if not success:
                    return answer_choices[0],False
                
            else:
                
                return random.choice(answer_choices),True


    if isinstance(memory_object,SimpleMemory):
        code_position=None
    else:
        code_position = get_code_position()
        
    memory_object.log_model_turn(raw_result,function_name,function_inputs,code_position=code_position,usage_log=usage_log,supervisor_info=supervisor_info)
    success = not(usage_log['model']=='failed')
    return result,success

def make_decision_regex(choices):
    """
    Create a minimal TGI response_format using a regex that restricts
    the output to exactly one of the enumerated choices.

    Example:
        >>> make_decision_regex(["apple", "banana", "cherry"])
        {
            "type": "regex",
            "pattern": "(apple|banana|cherry)"
        }

    Args:
        choices (list[str]): A list of allowed string outputs.

    Returns:
        dict: A TGI response_format dictionary for a single-choice regex.
    """
    # Build a pattern like: ^(apple|banana|cherry)$
    pattern = f"({'|'.join(choices)})"

    return {
        "type": "regex",
        "value": pattern
    }

# def make_decision_schema_json_tgi(choices, name="decision_schema"):
#     """
#     Create a JSON schema in the format:
#       {
#         "type": "json_schema",
#         "json_schema": {
#           "name": <name>,
#           "strict": True,
#           "value": {
#             "type": "object",
#             "properties": {
#               "answer": {
#                 "type": "string",
#                 "enum": [...]
#               }
#             },
#             "additionalProperties": false,
#             "required": ["answer"]
#           }
#         }
#       }

#     Args:
#         choices (list[str]): The allowed values for the "answer" property.
#         name (str): A unique name for the schema (default "decision_schema").

#     Returns:
#         dict: A Python dictionary representing the JSON schema.
#     """

#     schema = {
#         "type": "json",
#         "value":  {
#                 "type": "object",
#                 "properties": {
#                     "answer": {
#                         "type": "string",
#                         "enum": choices
#                     }
#                 },
#                 "additionalProperties": False,
#                 "required": ["answer"]
            
#         }
#     }
#     return schema
def make_decision_schema_json(choices, name="decision_schema"):
    """
    Create a JSON schema in the format:
      {
        "type": "json_schema",
        "json_schema": {
          "name": <name>,
          "strict": True,
          "schema": {
            "type": "object",
            "properties": {
              "answer": {
                "type": "string",
                "enum": [...]
              }
            },
            "additionalProperties": false,
            "required": ["answer"]
          }
        }
      }

    Args:
        choices (list[str]): The allowed values for the "answer" property.
        name (str): A unique name for the schema (default "decision_schema").

    Returns:
        dict: A Python dictionary representing the JSON schema.
    """

    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "enum": choices
                    }
                },
                "additionalProperties": False,
                "required": ["answer"]
            }
        }
    }
    return schema

def get_batch_embeddings(texts,default_size=4,**kwargs):
    """
    Gets embeddings for a batch of texts.

    Parameters:
    - texts (list of str): List of texts to embed.
    - default_size (str): used for test mode only, initialize random embedding of default_size.

    Returns:
    - list: Embeddings for the input texts.
    """
    #if model_type=='openai':
    func = apis.openai_models.get_batch_embeddings
    memory_object = get_memory()

    if not "model" in kwargs:
        kwargs["model"] = memory_object.config.embedding_path



    if memory_object.test_mode:
        results = [np.random.randn(default_size).tolist()]*len(texts)

    else:
        results = func(texts,**kwargs)
    return results

def get_single_embedding(text,default_size=1536,**kwargs):
    """
    Gets embedding for a single text.

    Parameters:
    - text (str): The text to embed.
    - default_size (str): used for test mode only, initialize random embedding of default_size.

    Returns:
    - list: Embedding for the input text.
    """
    memory_object = get_memory()
    if memory_object.test_mode:
        result = np.random.randn(default_size).tolist()

    else:
        if not "model" in kwargs:
            kwargs["model"] = memory_object.config.embedding_path
        #if model_type=='openai':
        func = apis.openai_models.get_single_embedding
        result = func(text,**kwargs)
        

    return result
# @supervisable(function_type='generation')
# def call_chat_completion(messages,model=None,**kwargs):

#     func = apis.openai_models.call_openai_chatbot

#     memory_object = get_memory()
#     config = memory_object.config

#     if "_forced_output" in kwargs:
#         usage_log=None
#         result =  kwargs['_forced_output']

#     else:
#         result,usage_log = func(messages=messages,model=model,**kwargs)
#         success=not(usage_log['model']=='failed')

#     function_name = "call_chat_completion"

#     function_inputs = {"messages":messages}
    
#     if isinstance(memory_object,SimpleMemory):
#         code_position=None
#     else:
#         code_position = get_code_position()
#     memory_object.log_model_turn(result,function_name,function_inputs,code_position=code_position,usage_log=usage_log)
    
#     return result,success


@supervisable(function_type='generation')
def call_completion(prompt,model=None,**kwargs):
    func = apis.openai_models.call_openai_completion

    memory_object = get_memory()
    config = memory_object.config

    if "_forced_output" in kwargs:
        usage_log=None
        result =  kwargs['_forced_output']
        supervisor_info= kwargs['_supervisor_info']
        success=True

    else:
        result,usage_log = func(prompt=prompt,model=model,**kwargs)
        success=not(usage_log['model']=='failed')
        supervisor_info=None
    function_name = "call_completion"

    function_inputs = {"prompt":prompt}
    
    if isinstance(memory_object,SimpleMemory):
        code_position=None
    else:
        code_position = get_code_position()
    memory_object.log_model_turn(result,function_name,function_inputs,code_position=code_position,usage_log=usage_log,supervisor_info=supervisor_info)
    
    return result,success


def completions_classifier(allowed_tokens, prompt=None,messages=None,model=None,**kwargs):
    func = apis.openai_models.completions_classifier


    memory_object = get_memory()
    config = memory_object.config

    supervisor_info=None
    result,usage_log = func(allowed_tokens=allowed_tokens,messages=messages,prompt=prompt,model=model,**kwargs)
    success=not(usage_log['model']=='failed')

    function_name = "completions_classifier"

    function_inputs = {"messages":messages}
    
    if isinstance(memory_object,SimpleMemory):
        code_position=None
    else:
        code_position = get_code_position()
    memory_object.log_model_turn(result,function_name,function_inputs,code_position=code_position,usage_log=usage_log,supervisor_info=supervisor_info)
    
    return result

def completions_logits(allowed_tokens, prompt=None,messages=None,model=None,**kwargs):
    func = apis.openai_models.logit_completions


    memory_object = get_memory()
    config = memory_object.config

    supervisor_info=None
    result,usage_log = func(allowed_tokens=allowed_tokens,messages=messages,prompt=prompt,give_logits=True,model=model,**kwargs)
    success=not(usage_log['model']=='failed')

    function_name = "completions_logits"

    function_inputs = {"messages":messages}
    
    if isinstance(memory_object,SimpleMemory):
        code_position=None
    else:
        code_position = get_code_position()
    memory_object.log_model_turn(result,function_name,function_inputs,code_position=code_position,usage_log=usage_log,supervisor_info=supervisor_info)
    
    return result
@supervisable(function_type='generation')
def call_chat_completion(messages,model=None,**kwargs):

    func = apis.openai_models. call_openai_chatbot

    memory_object = get_memory()
    config = memory_object.config

    if "_forced_output" in kwargs:
        usage_log=None
        result =  kwargs['_forced_output']
        supervisor_info= kwargs['_supervisor_info']
        success=True

    else:
        supervisor_info=None
        result,usage_log = func(messages=messages,model=model,**kwargs)
        success=not(usage_log['model']=='failed')

    function_name = "call_chat_completion"

    function_inputs = {"messages":messages}
    
    if isinstance(memory_object,SimpleMemory):
        code_position=None
    else:
        code_position = get_code_position()
    memory_object.log_model_turn(result,function_name,function_inputs,code_position=code_position,usage_log=usage_log,supervisor_info=supervisor_info)
    
    return result,success

@supervisable(function_type='generation')
def call_llm(prompt,call_type="chat_completion",model=None,**kwargs):


    prompt=apis.openai_models.truncate_prompt(prompt)
    if call_type=="chat_completion":

        result,success=call_chat_completion(messages=[{"role":"user","content":prompt}],model=model,**kwargs)
    elif call_type=="completion":
        result,success=call_completion(prompt=prompt,model=model,**kwargs)
    else:
        raise Exception(f"invalid call type {call_type}")
    return result[0]

    




def call_model(input_turns,output_turns,system_prompt,system_prompt_in_turns=False,model_type=None,model=None,multi_modal_inputs=None,**kwargs):
    """
    Calls a conversational model and returns its response.

    Parameters:
    - input_turns (list): Input conversation history.
    - output_turns (list): Output conversation history.
    - system_prompt (str): System prompt for the model.
    - system_prompt_in_turns (bool): Whether to include system prompt in conversation turns.
    - model_type (str, optional): Type of model to use.
    - model (str, optional): Path to the model.
    - multi_modal_inputs - list[dict] --list of open ai style image or audio inputs for the model, for example :
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"}
                    } 
    - **kwargs: Additional parameters for the model.

    Returns:
    - tuple: (model response, usage_log flag)
    """
    memory_object = get_memory()
    config = memory_object.config

    if model_type is None:
        model_type=memory_object.config.chatbot_type

   # if model_type=='openai':
    if "prefix" in kwargs:
        func = apis.openai_models.call_openai_completions
    else:
        func = apis.openai_models.call_openai_chatbot
        
    


    preprocess_func =apis.openai_models.get_chatbot_messages
    
        
    messages = preprocess_func(input_turns,output_turns,system_prompt,system_prompt_in_turns=system_prompt_in_turns,truncate_input=True,model=model,multi_modal_inputs=multi_modal_inputs)
    

    if "_forced_output" in kwargs:
        usage_log=None
        result =  kwargs['_forced_output']
        supervisor_info = kwargs["_supervisor_info"]
        success=True

    else:
        result,usage_log = func(messages=messages,model=model,**kwargs)
        success=not(usage_log['model']=='failed')
        supervisor_info =None

    function_name = "call_model"
    if "prefix" in kwargs:
        function_inputs = {"input_turns":input_turns,"output_turns":output_turns,"prefix":kwargs["prefix"],"system_prompt":system_prompt,"multi_modal_inputs":multi_modal_inputs}
    else:
        function_inputs = {"input_turns":input_turns,"output_turns":output_turns,"system_prompt":system_prompt,"multi_modal_inputs":multi_modal_inputs}
    
    if isinstance(memory_object,SimpleMemory):
        code_position=None
    else:
        code_position = get_code_position()
    memory_object.log_model_turn(result,function_name,function_inputs,code_position=code_position,usage_log=usage_log,supervisor_info=supervisor_info)
    
    return result,success

def generate_json_schema(questions_with_answers):
    """
    Generate a JSON schema dynamically from a list of questions and their answer sets.
    
    Args:
        questions_with_answers (list): A list of tuples (question, [valid_answers]).
        
    Returns:
        dict: The generated JSON schema.
    """
    properties = {}
    for question, answers in questions_with_answers:
        properties[question] = {
            "type": "string",
            "enum": answers,
            "description": "Choose one of the options"
        }
    
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys())
    }


        

def convert_openai_json_schema(schema):

    new_schema = {"type":"json","value":schema["json_schema"]["schema"]}
    return new_schema

@supervisable(function_type='json')
def generate_list_of_dicts(instruction,keys,**kwargs):
    """
    Generates a JSON Schema for a list of dictionaries.
    Each dictionary has fixed keys and string values.

    Parameters:
    - keys (list[str]): List of fields for each dictionary, each dictionary will have these fields

    Returns:
    - dict: JSON Schema representing the list of dictionaries.
    """
    # Create the schema for a single dictionary with all required keys

    properties = {key: {"type": "string"} for key in keys}  # Each key maps to a string
    item_schema = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,  # Disallow extra keys
        "required": list(keys)  # All keys in the set are required
    }
 
    

    inner_schema = {
                "type": "object",  # Root type must be an object
                "properties": {
                    "data": {  # The key under which the array is nested
                        "type": "array",
                        "items": item_schema  # Array of dictionaries with the defined schema
                    }
                },
                "required": ["data"],  # Ensure the "data" key is present
                "additionalProperties": False  # Disallow extra keys in the root object
            }
   # inner_schema = items_schema[0]

    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "list_of_fixed_dicts",
            "strict": True,
            "schema": inner_schema
        }
    }
    

    result = generate_object(instruction,schema,**kwargs)


    try:
     
        result=json.loads(result)
    except:
        result = initialize_with_defaults_json(schema)

    


    return result['data']






def decision_chain(instruction,chain,**kwargs):
    """
    Execute a series of multiple choice style decisions with one call to the model where each thought can have a different prompt. Uses structured outputs to force a sequence of constrained outputs. 
    Args:
        instruction (str): Instruction for the model
        chain list[str]: list of dictionaries, each each dictionary needs to have fields 'question' and 'choices', where question is a string and choices is a list of strings corresponding to multiple choice answers to the question.list of prompts for each thought
    Returns:
        output_list (list[str]): Gives the model generation for each prompt
    """

    for item in chain:
        item['type']='decision'
    
    return thought_decision_chain(instruction,chain,**kwargs)

def thought_chain(instruction,chain,**kwargs):
    """
    Execute a series of thoughts with one call to the model where each thought can have a different prompt 
    Args:
        instruction (str): Instruction for the model
        chain list[dict]: list of prompts for each thought
    Returns:
        output_list (list[str]): Gives the model's answer choice for each question as a list. Each output will correspond to one of the strings in choices

    """

    new_chain = [{"prompt":x,"type":"thought"} for x in chain]



    return thought_decision_chain(instruction,new_chain,**kwargs)




def thought_decision_chain(instruction,chain_structure,fixed_type = None,**kwargs):
    """
    Execute a series of thought and decision like actions in one call to the model using structured outputs
    
    Args:
        instruction (str): Instruction for the model
        chain_structure (list[dict]): a list of actions to be performed by the model. Each list contains a dict
            each dict in chain_structure dict must specify whether it is a 'decision' or 'thought' 
            example of of a 'thought': {'type': 'thought','prompt':str }
            example of of a 'decision': {'type': 'decision','question':str,'choices':list[str] }
            
        
    Returns:
        output_list (list[str]): A list with the result of each item in the chain structure. For thoughts in the chain, this will correspond to model output. For decisions in the chain , this will be one of the 'choices' field
    """

    item_definitions = dict()
    num_items=0
    all_prompts=[]
    all_decision_values=[]
    properties = {}
    prompt_mapping = list()
    for item in chain_structure:

        num_items+=1
        

        
        if item['type']=='decision':
            question= item['question']
            choices = item['choices']
 


            input_turns,output_turns,values =make_decision_prompt(turns=[],transition_question=question,answers=choices,max_turns=0)
            prompt=input_turns[0].replace("\n"," ")
            prompt=prompt.replace("\"","'")
            all_prompts.append(prompt)
            all_decision_values.append(values)
            if prompt in properties:
                raise Exception("No duplicate questions+answers allowed for thought_decision_chain")
            properties[prompt] = {
                "type": "string",
                "enum": list(values),
                "description": "Choose one of the options"
            }
    
           # item_definitions[f"item{num_items}"]=create_qa_object(prompt,values)

          

        elif  item['type']=='thought':
            if item['prompt'] in properties:
                raise Exception("No duplicate prommpts allowed for thought_decision_chain")
            prompt = item['prompt']
            prompt=prompt.replace("\n"," ")
            prompt=prompt.replace("\"","'")
            all_prompts.append(prompt)
            
            all_decision_values.append(None)
            #item_definitions[f"item{num_items}"]=create_prompt_object(item['prompt'])
            properties[prompt] = {
                "type": "string",

            }
  
        else:
            raise Exception("undefined item type for thought_decision_chain")
    # schema = {
    #     "type": "json_schema",
    #     "json_schema": {  # Nest your properties and required keys inside json_schema
    #         "name": "questionnaire_schema",
    #         "type": "object",
    #         "properties": properties,
    #         "required": list(properties.keys())
    #     }
    # }

    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "questionnaire_schema",  # Unique name for the schema
            "strict": True,
            "schema": {  # Encapsulate the schema here
                "type": "object",
                "properties": properties,
                "additionalProperties":False,
                "required": list(properties.keys())
            }
        }
    }
    result = generate_object(instruction,schema,**kwargs)

    try:
        result=json.loads(result)
    except:
        result = initialize_with_defaults_json(schema)

    output_list=[]
    outputs = list(result.values())
    

    for i in range(len(all_prompts)):
        item = chain_structure[i]


    
        output = outputs[i]
 
        if  item['type']=='decision':
            

            
            if output in all_decision_values[i]:
                index = all_decision_values[i].index(output)
            else:
                memory = get_memory()
                if memory.test_mode:
                    index = np.random.randint(len(all_decision_values[i]))
                
                else:
                
                    print("warning!!, multiple choice answer not parsed correctly")
                    index=0
            output_list.append(item['choices'][index])

        else:
            output_list.append(output)



    return output_list

#     )

@supervisable(function_type='json')
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

    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "list_of_strings",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "data": {  # The key under which the array is nested
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "additionalItems": False  # Disallow extra items in the array
                    }
                },
                "required": ["data"],  # Ensure the "data" key is present
                "additionalProperties": False  # Disallow extra keys in the root object
            }
        }
    }
        

    result = generate_object(instruction,schema,**kwargs)


    try:
        result=json.loads(result)
    except:
        result = initialize_with_defaults_json(schema)


    
    return result['data']
    
@supervisable(function_type='json')
def generate_list_of_choices(instruction,choices,**kwargs):
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

    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "list_of_strings",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "data": {  # The key under which the array is nested
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": choices
                        },
                        "additionalItems": False  # Disallow extra items in the array
                    }
                },
                "required": ["data"],  # Ensure the "data" key is present
                "additionalProperties": False  # Disallow extra keys in the root object
            }
        }
    }
        

    result = generate_object(instruction,schema,**kwargs)


    try:
        result=json.loads(result)
    except:
        result = initialize_with_defaults_json(schema)


    
    return result['data']

@supervisable(function_type='json')
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
    properties = {key: {"type": "string"} for key in keys}  # Each key maps to a string

    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "fixed_dict",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": properties,  # Keys with their expected types and constraints
                "additionalProperties": False,  # Disallow extra keys
                "required": list(keys)  # Ensure all keys are present
            }
        }
    }
    result = generate_object(instruction,schema,**kwargs)


    try:
        result=json.loads(result)
    except:
        result = initialize_with_defaults_json(schema)

    return result

@supervisable(function_type='json')
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
    fields = [f'item{i}' for i in range(1,num_items+1)]

    result = generate_fixed_dict(instruction, fields, **kwargs)


    out_list = [result[f'item{i}'] for i in range(1,num_items+1)]
   
    return out_list





    
def generate_list_obj(instruction,**kwargs):
    """
    Generates a list based on the given instruction using a predefined list structure.

    Parameters:
    - instruction (str): The instruction for generating the list.
    - **kwargs: Additional arguments for model configuration.

    Returns:
    - list[str]: A list of generated items.
    """
    print("warning, generate_list_obj is deprecated and may be removed.")
    memory_object = get_memory()
    config = memory_object.config

    class SimpleList(BaseModel):
        items: list[str]



    result = generate_object(instruction,SimpleList,**kwargs)

    
    return result.items



def generate_fixed_list_obj(instruction,num_items,**kwargs):
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

def generate_fixed_dict_obj(instruction, keys, **kwargs):
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
    if "max_turns" in kwargs:
        max_turns = kwargs['max_turns']
        del kwargs['max_turns']
    else:
        max_turns = None

    memory_object = get_memory()
    config = memory_object.config
    #obj_structure = convert_openai_json_schema(obj_structure)

    if not config.chatbot_type=="openai":
        instruction+=f"\nYour output must adhere to the following json schema: {obj_structure}"


    input_turns,output_turns,system_prompt = get_turn_history(instruction=instruction,max_turns=max_turns)
    memory_object = get_memory()
    if not memory_object.test_mode:


        result= call_object_model(input_turns,output_turns,system_prompt,system_prompt_in_turns=memory_object.config.system_prompt_in_turns,obj_structure=obj_structure,**kwargs)
        return result
    else:
        if isinstance(obj_structure, dict):
            return initialize_with_defaults_json(obj_structure)
        else:

            return initialize_with_defaults(obj_structure)
    
def call_object_model(input_turns,output_turns,system_prompt,system_prompt_in_turns=False,model_type=None,model=None,obj_structure=None,multi_modal_inputs=None,**kwargs):
    """
    Calls a model to generate an object formatted response.

    Parameters:
    - input_turns (list): Input conversation history.
    - output_turns (list): Output conversation history.
    - system_prompt (str): System prompt to guide the model.
    - system_prompt_in_turns (bool): Whether to include the system prompt in conversation turns.
    - model_type (str, optional): Type of model to use.
    - model (str, optional): Path to the model.
    - obj_structure (BaseModel): Structure for the expected response.
    - multi_modal_inputs - list[dict] --list of open ai style image or audio inputs for the model, for example :
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"}
                    } 
    - **kwargs: Additional parameters for the model.

    Returns:
    - obj_structure: An instance of the specified object structure with generated values.
    """

 

    memory_object = get_memory()
    config = memory_object.config

    if model_type is None:
        model_type=memory_object.config.chatbot_type

    #if model_type=='openai' or model_type=="proxy":

    func = apis.openai_models.call_openai_chat_formatted

    preprocess_func =apis.openai_models.get_chatbot_messages

   

    

    
    

    

    # if not config.chatbot_type=="openai":
        
    #     if isinstance(obj_structure, dict):
            
    #         obj_structure = convert_openai_json_schema(obj_structure)
    #     else:
    #         obj_structure=obj_structure.schema()
    #         if obj_structure['type']=="object":
    #             obj_structure['type']="json"


        
    messages = preprocess_func(input_turns,output_turns,system_prompt,system_prompt_in_turns=system_prompt_in_turns,truncate_input=True,model=model,multi_modal_inputs=multi_modal_inputs)

    if "_forced_output" in kwargs:
        result = kwargs["_forced_output"]
        raw_str = kwargs["_forced_output"]
        supervisor_info = kwargs["_supervisor_info"]

        usage_log=None
    else:
        result,raw_str,usage_log = func(messages,model=model,obj_structure = obj_structure,**kwargs)
        supervisor_info = None


    


    function_name = "call_object_model"
    function_inputs = {"input_turns":input_turns,"output_turns":output_turns,"system_prompt":system_prompt,"multi_modal_inputs":multi_modal_inputs,'obj_structure':obj_structure}
    if isinstance(memory_object,SimpleMemory):
        code_position=None
    else:
        code_position = get_code_position()


    if usage_log['model']=='failed':
        if isinstance(obj_structure, dict):
            if 'value' in obj_structure:
                result = initialize_with_defaults_json(obj_structure['value'])
            else:
                result = initialize_with_defaults_json(obj_structure)
        else:
            result = initialize_with_defaults(obj_structure)
    else:
        memory_object.log_model_turn(raw_str,function_name,function_inputs,code_position=code_position,usage_log=usage_log,supervisor_info=supervisor_info)
    return result


def initialize_with_defaults_json(schema):
    """
    Initializes a dictionary with default values based on a JSON Schema.

    Parameters:
    - schema (dict): The JSON Schema to process.

    Returns:
    - dict: A dictionary with default values for all fields in the schema.
    """
    defaults = {}

    if not 'json_schema' in schema:
        schema = {'json_schema':{'schema':schema}}
    

    # Iterate through properties in the schema
    for field_name, field_props in schema['json_schema']['schema'].get("properties", {}).items():
        field_type = field_props.get("type")
        
        # Set default value based on the field type
        if field_type == "string":
            defaults[field_name] = "<There was an error generating this message, please ignore>"
        elif field_type == "integer":
            defaults[field_name] = 0
        elif field_type == "number":  # Includes floats
            defaults[field_name] = 0.0
        elif field_type == "boolean":
            defaults[field_name] = False
        elif field_type == "array":
            defaults[field_name] = []
        elif field_type == "object":
            # Recursively initialize nested objects
            nested_schema = field_props
            defaults[field_name] = initialize_with_defaults_json(nested_schema)
        elif "enum" in field_props:
            # Use the first enum value as the default
            defaults[field_name] = field_props["enum"][0]
        else:
            defaults[field_name] = None  # Default to None for any other type

    return defaults


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
        field_type = field.annotation  # Updated to use field.annotation
        origin = getattr(field_type, '__origin__', None)
        args = getattr(field_type, '__args__', ())

        # Set default value based on the type
        if field_type == str:
            defaults[field_name] = "<There was an error generating this message, please ignore>"
        elif field_type == int:
            defaults[field_name] = 0
        elif field_type == float:
            defaults[field_name] = 0.0
        elif field_type == bool:
            defaults[field_name] = False
        elif origin == list:
            # Generate a random list with elements of the appropriate type
            list_type = args[0] if args else str  # Default to str if no type is specified
            defaults[field_name] = [
                initialize_value(list_type) for _ in range(np.random.randint(0, 5))
            ]
        elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
            # Recursively initialize nested models
            defaults[field_name] = initialize_with_defaults(field_type)
        else:
            defaults[field_name] = None  # Use None for any other type

    return model_class.construct(**defaults)
def initialize_value(value_type):
    """
    Generate a default value for a given type.
    """
    if value_type == str:
        return "<default>"
    elif value_type == int:
        return 0
    elif value_type == float:
        return 0.0
    elif value_type == bool:
        return False
    elif isinstance(value_type, type) and issubclass(value_type, BaseModel):
        return initialize_with_defaults(value_type)
    else:
        return None  # Default to None for unknown types



def set_system_prompt(text):
    """
    Sets the system prompt for the current memory object at the current autograms function level.

    Parameters:
    - text (str): The system prompt text.
    """
    memory_object = get_memory()
    memory_object.set_system_prompt(text)

def get_system_prompt():
    """
    Sets the system prompt for the current memory object at the current autograms function level.

    Parameters:
    - text (str): The system prompt text.
    """
    memory_object = get_memory()
    return memory_object.get_system_prompt()

def append_system_prompt(text):
    """
    Appends the system prompt for the current memory object at the current autograms function level.

    Parameters:
    - text (str): The system prompt text.
    """
    memory_object = get_memory()
    orig = memory_object.get_system_prompt()
    memory_object.set_system_prompt(orig+"\n"+text)



    
def get_turn_history(instruction="",max_turns=None,conv_only=False):
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
    

    inputs,outputs= make_prompt(turns,instruction,max_turns=max_turns,transition=False)
   

    return inputs,outputs,system_prompt



def extract_last_user_reply():
    """
    Extracts the last submitted user reply
    Returns:
    - user_reply(str)
    """
    memory_object = get_memory()
    return memory_object.get_user_reply()

def extract_full_conv_history():
    """
    Extracts the conversation history
    Returns:
    - conv_history (List[dict]): A list of all conversation turns between the model and the user
    """
    memory_object = get_memory()
    return memory_object.extract_full_conv_history()


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




def extract_code(input_string, code_type='python', merge_blocks=True):
    """
    Extract code from fenced code blocks of a specified type in the input string,
    ignoring any nested fences until the top-level block is closed.

    Args:
        input_string (str): The input string containing text and code blocks.
        code_type (str): The type of code to extract (e.g., 'python', 'javascript').
        merge_blocks (bool): If True, merge all extracted blocks into a single string
                             separated by newlines. Otherwise, return a list of blocks.

    Returns:
        str or list: The extracted code. A single string if merge_blocks=True,
                     otherwise a list of individual code block strings.
    """
    # We'll identify lines that start with the exact fence:
    # - opening for the specified language: ```python (with optional trailing spaces)
    # - any triple backticks (```...) to track nesting or closing
    start_pattern = re.compile(rf'^```{re.escape(code_type)}\s*$')
    any_fence_pattern = re.compile(r'^```\s*(\S+)?\s*$')  # captures language if present

    lines = input_string.splitlines(keepends=True)
    code_blocks = []
    current_block_lines = []
    
    in_block = False
    depth = 0

    for line in lines:
        if not in_block:
            # Look for the start of a block with the given language
            if start_pattern.match(line.strip()):
                # We've found an opening fence of the correct language
                in_block = True
                depth = 1  # top-level open
                # We don't add the fence line itself to the code
            else:
                # Outside of any block; do nothing
                continue
        else:
            # We are inside a code block
            fence_match = any_fence_pattern.match(line.strip())
            if fence_match:
                # This line is some form of ``` fence
                language_found = fence_match.group(1)  # e.g. 'python', 'js', etc.

                # Check if it's an opening fence for the same language
                # or just a closing fence (``` with no language or different language)
                if language_found == code_type:
                    # Another nested opening
                    depth += 1
                    current_block_lines.append(line)  # Keep the fence in the code if desired
                else:
                    # This is presumably a closing fence for the current nesting level
                    depth -= 1
                    if depth == 0:
                        # We've closed the top-level block
                        # finalize the current block
                        code_blocks.append(''.join(current_block_lines))
                        current_block_lines = []
                        in_block = False
                    else:
                        # It's a nested fence, but not the top-level close yet
                        current_block_lines.append(line)
            else:
                # Just a normal line inside the code block
                current_block_lines.append(line)

    # If a block never got closed, you could optionally decide to include it:
    # if in_block and current_block_lines:
    #     code_blocks.append(''.join(current_block_lines))

    if merge_blocks:
        return "\n".join(code_blocks)
    else:
        return code_blocks




def extract_code_legacy(input_string, code_type='python',merge_blocks=True):
    """
    Extract and concatenate code from multiple code blocks of a specified type in the input string.

    Args:
        input_string (str): The input string containing text and code blocks.
        code_type (str): The type of code to extract (e.g., 'python', 'javascript'). Defaults to 'python'.

    Returns:
        str: The concatenated code from all specified code blocks, separated by newlines.
    """
    # Regular expression to find all ```<code_type>``` code blocks
    pattern = rf'```{re.escape(code_type)}\n(.*?)```'
    code_blocks = re.findall(pattern, input_string, re.DOTALL)
    # Join the extracted blocks with newlines
    if merge_blocks:
        return '\n'.join(code_blocks)
    else:
        return code_blocks

def execute_code(code, command="firejail --noprofile --quiet --read-only=/home --read-only=/usr python3",timeout=60,code_suffix=".py"):
  
    """
    Execute Python (or other code) code in a sandboxed environment.

    Args:
        code (str): The Python code to execute.
        command (str): The command to execute the Python code, wrapped in a sandbox. Defaults to Firejail.

    Returns:
        tuple: A tuple containing:
            - message (str): Output messages, including stdout, stderr, or timeout messages.
            - success (bool): True if execution completed successfully, False otherwise.
    """
    


    if (not timeout is None) and timeout>0:
        # Add timeout to the command
        command_with_timeout = f"timeout {timeout} {command}"
    else:
        command_with_timeout =command

    # Create a temporary file for the Python code
    with tempfile.NamedTemporaryFile(suffix=code_suffix, delete=False) as temp_file:
        temp_file.write(code.encode("utf-8"))
        temp_file_path = temp_file.name

    try:
        # Execute the code using the sandbox command
        result = subprocess.run(
            f"{command_with_timeout} {temp_file_path}",
            shell=True,
            text=True,
            capture_output=True,
             bufsize=4096
        )

        # Process the result
        if result.returncode == 0:
            return result.stdout, True
        elif result.returncode == 124:  # Timeout return code
            return f"Execution timed out after {timeout} seconds. Code needs to run faster to be executable with these sandboxed run settings for autograms.functional.execute_python. If you are an LLM being asked to write code, the timeout command was added on purpose and you need to try to write code that runs faster.", False
        else:
            return result.stderr, False

    except Exception as e:
        return str(e), False

    finally:
        # Ensure the temporary file is deleted
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)




def parallel_wrapper(function, arg_list, mem_list=None,with_autograms_memory=True):
    """
    Parallel wrapper for running a function with arguments in multiple processes.
    - Initializes thread-local state for each process.
    - Returns function results and final thread-local states.

    Args:
    - function (callable): The function to be executed.
    - arg_list (list): List of argument dictionaries for each function call.
    - mem_list (list or None): Optional list of serialized memory objects for each task.

    Returns:
    - results (list): List of function results.
    - final_states (list): List of final thread-local states from each process.
    """
    if with_autograms_memory:
        shared_memory = dill.dumps(get_memory())  # Retrieve thread-local shared memory
    else:
        shared_memory=None

    if mem_list is not None and len(mem_list) != len(arg_list):
        raise ValueError("mem_list must be the same length as arg_list if provided.")

    with ProcessPoolExecutor() as executor:
        try:
            futures = [
                executor.submit(
                    process_task,
                    dill.dumps(function),
                    arg_list[i],
                    shared_memory if mem_list is None else mem_list[i]
                )
                for i in range(len(arg_list))
            ]
            results = [future.result() for future in futures]
        except Exception as e:
            print(f"Error during parallel execution: {e}")
            raise
    return results


def initialize_thread_local(shared_object):
    """
    Initialize the thread-local variable with a deep copy of the shared object.
    """
    set_memory(shared_object)

def process_task(function_pkl, args, shared_object_encoding=None):
    """
    Wrapper function for each process to:
    1. Initialize thread-local variable.
    2. Call the provided function with arguments.
    """
    function = dill.loads(function_pkl)
    if not shared_object_encoding is None:
        shared_object = dill.loads(shared_object_encoding)
        initialize_thread_local(shared_object)
    result = function(**args)

    if isinstance(result, AutogramsReturn):

        result.memory = dill.dumps(result.memory)

   
    return result


def get_code_position():
    frame_info = find_decorated_frame()
    if frame_info is None:
        return None


    line_number = frame_info.lineno  # Absolute line number in the file
    function_name = frame_info.function

    return {"line_number":line_number,"function_name":function_name,"file_name":frame_info.filename}











