### Generation Functions

Generation functions indirectly manage calls to models as well as logging of turns for future use in prompts. They can be used to produce normal string outputs as well as structured outputs via Pydantic.



#### **thought(instruction)**
`autograms.functional.thought`
Generates a thought response that is logged but not displayed to the user.

- **Parameters**:
  - `instruction` (str): Instruction to guide the thought response.

- **Returns**:
  - `str`: The generated thought.

#### **silent_thought(instruction)**
`autograms.functional.silent_thought`
Generates a thought response without logging it.

- **Parameters**:
  - `instruction` (str): Instruction to guide the thought response.

- **Returns**:
  - `str`: The generated thought.

#### **generate_list_of_dicts(instruction, keys, `**kwargs`)**
`autograms.functional.generate_list_of_dicts`  
Generates a list of dictionaries with fixed keys and string values based on the provided instruction.

- **Parameters**:
  - `instruction` (str): Instruction to guide the list generation.
  - `keys` (list[str]): List of fields for each dictionary. Each dictionary will include these fields as keys.

- **Returns**:
  - `list[dict]`: A list of dictionaries where each dictionary has the specified keys with string values.

---

#### **thought_chain(instruction, chain, `**kwargs`)**
`autograms.functional.thought_chain`  
Executes a series of thoughts in one call to the model, where each thought can have a different prompt.

- **Parameters**:
  - `instruction` (str): Instruction to guide the thought chain.
  - `chain` (list[dict]): A list of prompts for each thought in the chain.

- **Returns**:
  - `list[str]`: A list of generated responses, with each response corresponding to a prompt in the chain.

---

#### **thought_decision_chain(instruction, chain_structure, fixed_type=None, `**kwargs`)**
`autograms.functional.thought_decision_chain`  
Executes a series of actions (thoughts or decisions) in one call to the model, using a structured output schema.

- **Parameters**:
  - `instruction` (str): Instruction to guide the thought-decision chain.
  - `chain_structure` (list[dict]): A list of actions to be performed. Each action must specify its type as either `thought` or `decision`.
    - `thought` example: `{'type': 'thought', 'prompt': <str>}`
    - `decision` example: `{'type': 'decision', 'question': <str>, 'choices': <list[str]>}`
  - `fixed_type` (optional): Specifies a fixed type for all items in the chain. Defaults to `None`.

- **Returns**:
  - `list[str]`: A list of results for each item in the chain. For thoughts, this will be the model output. For decisions, this will be one of the provided choices.


#### **generate_list(instruction, `**kwargs`)**
`autograms.functional.generate_list`
Generates a list based on the given instruction.

- **Parameters**:
  - `instruction` (str): The instruction for generation.
  - `**kwargs`: Additional arguments for the model.

- **Returns**:
  - `list[str]`: A list of generated items.

#### **generate_fixed_list(instruction, num_items, `**kwargs`)**
`autograms.functional.generate_fixed_list`
Generates a list with a fixed number of items.

- **Parameters**:
  - `instruction` (str): Instruction for generation.
  - `num_items` (int): Number of items in the list.
  - `**kwargs`: Additional arguments for the model.

- **Returns**:
  - `list[str]`: A fixed-size list.

#### **generate_fixed_dict(instruction, keys, `**kwargs`)**
`autograms.functional.generate_fixed_dict`
Generates a dictionary with fixed keys.

- **Parameters**:
  - `instruction` (str): Instruction for generation.
  - `keys` (list[str]): Keys for the dictionary.
  - `**kwargs`: Additional arguments for the model.

- **Returns**:
  - `dict`: A dictionary with generated values.

#### **generate_object(instruction, obj_structure, `**kwargs`)**
`autograms.functional.generate_object`
Generates an object based on the given instruction and model structure.

- **Parameters**:
  - `instruction` (str): Instruction for generation.
  - `obj_structure` (BaseModel): Pydantic model structure.
  - `**kwargs`: Additional arguments.

- **Returns**:
  - `BaseModel`: Generated object.