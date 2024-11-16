### Prompt and History Functions
Located in `autograms.functional`.

#### **set_system_prompt(text)**
`autograms.functional.set_system_prompt`
Sets the system prompt in memory.

- **Parameters**:
  - `text` (str): The system prompt text.

#### **get_turn_history(instruction="", max_turns=-1, conv_only=False)**
`autograms.functional.set_turn_history`
Retrieves the conversation history formatted for the model.

- **Parameters**:
  - `instruction` (str): Instruction for the current turn.
  - `max_turns` (int): Maximum turns to include.
  - `conv_only` (bool): Whether to include only conversation turns.

- **Returns**:
  - `tuple`: Input turns, output turns, and system prompt.