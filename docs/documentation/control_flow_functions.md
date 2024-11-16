### Control Flow Functions


Control flow functions enable dynamic navigation within the Autograms chatbot and are meant to be used within @autograms_functions in order to jump to @autograms_nodes with predefined addresses. They manage transitions between different points in a conversation or program logic. They are not strictly necessary since careful application of loops, conditionals, and variables should be able to achieve any arbitrary graph, however they do make complex stateful chatbots easier to implement with the desired graph logic. GOTO statements are not normally allowed in python, but are possible in @autograms_functions using a combination of special exceptions and dynamic abstract syntax tree manipulation.

#### **TRANSITION(transition_question, transitions, max_turns=1, **kwargs)**
`autograms.functional.TRANSTION`
Manages a transition based on multiple-choice input.

- **Parameters**:
  - `transition_question` (str): The question prompting the transition.
  - `transitions` (dict): Maps choices to their corresponding addresses.
  - `max_turns` (int): Maximum attempts for a valid response.
  - `**kwargs`: Additional arguments for the model.

- **Raises**:
  - `GoTo`: To jump to the target address.

#### **EXIT(data={})**
`autograms.functional.EXIT`
Exits the current function and returns the provided data.

- **Parameters**:
  - `data` (dict): Data to be returned.

- **Raises**:
  - `FunctionExit`: Used to exit the current function.

#### **GOTO(destination)**
`autograms.functional.GOTO`
Jumps to a specific address within the function.

- **Parameters**:
  - `destination` (str): Target address for the jump.

- **Raises**:
  - `GoTo`: Used to jump to the specified address.

#### **RETURNTO(destination)**
`autograms.functional.RETURNTO`
Returns to an address within an earlier function in the call stack.

- **Parameters**:
  - `destination` (str): Target address for returning.

- **Raises**:
  - `ReturnTo`: Used to return to the specified address.
