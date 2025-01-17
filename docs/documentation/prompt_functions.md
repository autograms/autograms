### Prompt and History Functions
Located in `autograms.functional`.

#### **set_system_prompt(text)**
`autograms.functional.set_system_prompt`
Sets the system prompt in memory. The system prompt will be reset to the calling scopes system prompt when a non-root function returns.

- **Parameters**:
  - `text` (str): The system prompt text.

#### **append_system_prompt()**
`autograms.functional.append_system_prompt`
Appends the system prompt in memory. When calling a new @autograms_function, the system prompt is inherited from the calling scope. Sometimes its desiable for the system prompt within a function to be appended to the original. The system prompt then resets back to the calling scope after the inner function returns.

- **Parameters**:
  - `text` (str): The system prompt text.

#### **get_system_prompt()**
`autograms.functional.get_system_prompt`
Gets the system prompt in memory. 

- **Returns**:
  - `text` (str): The system prompt text.



#### **get_turn_history(instruction="", max_turns=-1, conv_only=False)**
`autograms.functional.get_turn_history`
Retrieves the conversation history formatted for the model.

- **Parameters**:
  - `instruction` (str): Instruction for the current turn.
  - `max_turns` (int): Maximum turns to include.
  - `conv_only` (bool): Whether to include only conversation turns.

- **Returns**:
  - `tuple`: Input turns, output turns, and system prompt.



#### **extract_full_conv_history()**
`autograms.functional.extract_full_conv_history`
Extracts the conversation history between the model and the user. It ignores internal thought turns as well as the current position and scope of the stack. It is the cleanest way to extract a simple conversation history. It returns a list of dicts, where each dict has `"role"` (user/assistant) and `"content"` (reply). While autograms is generally designed so that the conversation history prompts are managed automatically, you can also extract the conversation to manage the prompts however you want and use them to call models directly.
- **Returns**:
  - `list[dict]`: A list of all conversation turns between the model and the user

### **extract_last_user_reply()**
Extracts the last submitted user reply, or None if the conversation hasn't started.
- **Returns**:
   - `str`: last submited user reply given with `memory_object.add_user_reply`. This typically happens automatically if you pass a `user_reply` argument to `autogram.reply` or `autogram.apply`




