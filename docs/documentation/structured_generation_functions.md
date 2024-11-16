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

#### **generate_list(instruction, **kwargs)**
`autograms.functional.generate_list`
Generates a list based on the given instruction.

- **Parameters**:
  - `instruction` (str): The instruction for generation.
  - `**kwargs`: Additional arguments for the model.

- **Returns**:
  - `list[str]`: A list of generated items.

#### **generate_fixed_list(instruction, num_items, **kwargs)**
`autograms.functional.generate_fixed_list`
Generates a list with a fixed number of items.

- **Parameters**:
  - `instruction` (str): Instruction for generation.
  - `num_items` (int): Number of items in the list.
  - `**kwargs`: Additional arguments for the model.

- **Returns**:
  - `list[str]`: A fixed-size list.

#### **generate_fixed_dict(instruction, keys, **kwargs)**
`autograms.functional.generate_fixed_dict`
Generates a dictionary with fixed keys.

- **Parameters**:
  - `instruction` (str): Instruction for generation.
  - `keys` (list[str]): Keys for the dictionary.
  - `**kwargs`: Additional arguments for the model.

- **Returns**:
  - `dict`: A dictionary with generated values.

#### **generate_object(instruction, obj_structure, **kwargs)**
`autograms.functional.generate_object`
Generates an object based on the given instruction and model structure.

- **Parameters**:
  - `instruction` (str): Instruction for generation.
  - `obj_structure` (BaseModel): Pydantic model structure.
  - `**kwargs`: Additional arguments.

- **Returns**:
  - `BaseModel`: Generated object.