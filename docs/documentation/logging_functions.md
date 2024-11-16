### Logging Functions

Logging functions are responsible for recording conversation turns and internal reasoning turns in the Autograms chatbot. They are used to save information that helps form prompts.

#### **log_chat_turn(reply, instruction=None, line_number=None, function_name=None)**
`autograms.functional.log_chat_turn`
Logs a user-visible chat turn in the memory object.

- **Parameters**:
  - `reply` (str): The agent's reply.
  - `instruction` (str, optional): Instruction context for the reply.
  - `line_number` (int, optional): Line number of the reply.
  - `function_name` (str, optional): Function name where the reply was generated.

#### **log_thought_turn(reply, instruction)**
`autograms.functional.log_thought_turn`
Logs a non-visible "thought" turn in the memory object.

- **Parameters**:
  - `reply` (str): The agent's internal thought response.
  - `instruction` (str): Instruction context for the thought.