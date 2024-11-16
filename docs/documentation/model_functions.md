### Model-Calling Functions


Model calling functions interface with external conversational or classification models. They prepare the input, send it to the model, and handle the response.

#### **call_conv_model(instruction)**
`autograms.functional.call_conv_model`
Calls the conversational model with the specified instruction.

- **Parameters**:
  - `instruction` (str): Instruction for the conversational model.

- **Returns**:
  - `str`: The model's response.

#### **call_classifier(input_str, answer_choices, model_type=None, model_path=None, **kwargs)**
`autograms.functional.call_classifier`
Calls a classification model to determine the best choice.

- **Parameters**:
  - `input_str` (str): The input text for classification.
  - `answer_choices` (list[str]): Possible answers.
  - `model_type` (str, optional): Type of the model.
  - `model_path` (str, optional): Path to the model.
  - `**kwargs`: Additional model arguments.

- **Returns**:
  - `tuple`: The chosen answer and a success flag.

#### **call_model(input_turns, output_turns, system_prompt, system_prompt_in_turns=False, model_type=None, model_path=None, **kwargs)**
`autograms.functional.call_model`
Calls a conversational model and retrieves a response.

- **Parameters**:
  - `input_turns` (list): The conversation input turns.
  - `output_turns` (list): The conversation output turns.
  - `system_prompt` (str): System prompt to guide the model.
  - `system_prompt_in_turns` (bool, default=False): Whether the system prompt is included in the turns.
  - `model_type` (str, optional): The type of model to call.
  - `model_path` (str, optional): Path to a specific model.
  - `**kwargs`: Additional arguments for the model.

- **Returns**:
  - `tuple`: A tuple containing:
    - `result` (str): The model response.
    - `success` (bool): Whether the model call was successful.

#### **call_object_model(input_turns, output_turns, system_prompt, system_prompt_in_turns=False, model_type=None, model_path=None, obj_structure=None, **kwargs)**
`autograms.functional.call_object_model`
Calls a model to generate a structured object based on input.

- **Parameters**:
  - `input_turns` (list[dict]): User input history.
  - `output_turns` (list[dict]): Model output history.
  - `system_prompt` (str): The system prompt.
  - `system_prompt_in_turns` (bool): Include system prompt in turns.
  - `model_type` (str, optional): Model type.
  - `model_path` (str, optional): Model path.
  - `obj_structure` (BaseModel): Pydantic model structure.
  - `**kwargs`: Additional arguments.

- **Returns**:
  - `BaseModel`: Generated object.