

from . import functional as F
from .program_control import  autograms_node

@autograms_node
def reply_instruction(instruction,ADDRESS=None):
    """
    Sends a reply generated by the model based on an instruction.

    Parameters:
    - instruction (str): Instruction guiding the model's response.
    - ADDRESS (str, optional): Address for jumping to this node.

    Raises:
    - ReplyExit: To exit with a reply.
    """
    F.reply_instruction(instruction)



@autograms_node
def reply_suffix(instruction,ADDRESS=None):
    """
    Sends a reply generated by the model and appends specific text at the end.

    Parameters:
    - instruction (str): Instruction specifying the suffix to append.
    - ADDRESS (str, optional): Address for jumping to this node.

    Raises:
    - ReplyExit: To exit with a reply.
    """
    F.reply_suffix(instruction)



@autograms_node
def reply(text,ADDRESS=None):    
    """
    Sends a direct reply.

    Parameters:
    - text (str): The reply text to be sent.
    - ADDRESS (str, optional): Address for jumping to this node.

    Raises:
    - ReplyExit: To exit with a reply.
    """
    F.reply(text)
    


@autograms_node
def location(ADDRESS=None):
    """
    Defines an empty node to serve as a placeholder or marker.

    Parameters:
    - ADDRESS (str, optional): Address for jumping to this node.
    """    
    pass

@autograms_node
def as_node(func,ADDRESS=None,*args,**kwargs):
    """
    Calls an existing function and makes it addressable as a node.

    Parameters:
    - func (callable): The function to wrap as a node.
    - ADDRESS (str, optional): Address for jumping to this node.
    - *args: Positional arguments for the function.
    - **kwargs: Keyword arguments for the function.

    Returns:
    - Any: The return value of the wrapped function.
    """
    result = func(*args,**kwargs)
    return result


@autograms_node
def TRANSITION(transition_question,transitions,max_turns=1,ADDRESS=None,**kwargs):
    """
    Directs the conversation based on a multiple-choice decision.

    Parameters:
    - transition_question (str): Question to present to the model.
    - transitions (dict): Mapping of choices to addresses.
    - max_turns (int): Maximum number of turns for the decision process.
    - ADDRESS (str, optional): Address for jumping to this node.
    - **kwargs: Additional arguments for the decision process.

    Raises:
    - GoTo: To jump to the address of the selected transition.
    """
    F.TRANSITION(transition_question,transitions,max_turns=1,**kwargs)




@autograms_node
def silent_thought(instruction,ADDRESS=None):
    """
    Executes a model-generated thought without logging it.

    Parameters:
    - instruction (str): Instruction for the model to generate a thought.
    - ADDRESS (str, optional): Address for jumping to this node.

    Returns:
    - str: The thought generated by the model.
    """
    response=F.silent_thought(instruction)


    return response

@autograms_node
def thought(instruction,ADDRESS=None):
    """
    Executes a model-generated thought and logs it.

    Parameters:
    - instruction (str): Instruction for the model to generate a thought.
    - ADDRESS (str, optional): Address for jumping to this node.

    Returns:
    - str: The thought generated by the model.
    """
    response =F.silent_thought(instruction)

    return response




# @autograms_node
# def save_program_state(file_name,ADDRESS=None):
#     #log memory and save it
#     pass

# @autograms_node
# def interrupt_and_state(data,ADDRESS=None):
#     #log memory and save it
#     pass


    