### Decision Functions

Decision functions are used to make choices within the Autograms chatbot. They use a restricted set of logits to force an LLM to chose from a limited set of choices. This enables an LLM to determine branch points in the program. 

#### **yes_or_no(question, max_turns=1, **kwargs)**
`autograms.functional.yes_or_no`
Asks the agent a yes-or-no question.

- **Parameters**:
  - `question` (str): The yes-or-no question.
  - `max_turns` (int): Maximum attempts for a valid response.
  - `**kwargs`: Additional arguments for the model.

- **Returns**:
  - `bool`: `True` for "Yes", `False` for "No".

#### **multiple_choice(question, choices, max_turns=1, **kwargs)**
`autograms.functional.multiple_choice`
Presents the agent with a multiple-choice question.

- **Parameters**:
  - `question` (str): The question to ask.
  - `choices` (list[str]): List of possible choices.
  - `max_turns` (int): Maximum attempts for a valid response.
  - `**kwargs`: Additional arguments for the model.

- **Returns**:
  - `int`: Index of the selected choice.

#### **decision_chain(instruction,chain,**kwargs)**
`autograms.functional.decision_chain`
Execute a series of multiple choice style decisions with one call to the model where each thought can have a different prompt. Uses structured outputs to force a sequence of constrained outputs.
- **Parameters**:
   
  - instruction (str): Instruction for the model
  - chain list[str]: list of dictionaries, each each dictionary needs to have fields 'question' and 'choices', where question is a string and choices is a list of strings corresponding to multiple choice answers to the question.list of prompts for each thought
- **Returns**:
    output_list (list[str]): Gives the model generation for each prompt
