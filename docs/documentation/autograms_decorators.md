
## `@autograms_function()`

The `@autograms_function()` decorator is a core feature of the Autograms framework, designed to enable dynamic control flow in conversational agents. It transforms standard Python functions into resumable, stateful workflows that can pause, serialize, and resume seamlessly. This allows chatbots or other interactive agents to act as one continuously running program that can be paused and saved at any time while waiting for input.

### Key Features
1. **Pause and Resume Execution**:  
   Functions decorated with `@autograms_function()` can pause at any point using special nodes (e.g., `reply`, `reply_instruction`). These pauses return temporary responses to the user, while the function's state is saved and can be resumed from the exact point it left off.


2. **Memory management**:  
   The function’s local variables, call stack, and conversation history are managed through an internal memory object, enabling serialization and reloading across different sessions.

3. **Conversation Scopes**:  
   Manage how conversation history is retained using flexible scope options (`global`, `normal`, `local`).


4. **Dynamic Control Flow**:  
   The decorator supports advanced control mechanisms like GOTO and RETURNTO, allowing the program to jump to specific points in the function based on predefined `ADDRESS` labels in functions decorated by `@autograms_node`.

---

### Parameters
- **conv_scope** (str, optional):  
  Defines the conversation scope. Defaults to `"global"`.
  - `"global"`: Turns persist and are accessible across all nested calls.
  - `"normal"`: Turns are accessible within the current function but do not persist after returning.
  - `"local"`: Turns are isolated to the current function call.

---







### Example usage

```
from autograms.nodes import reply, reply_instruction
from autograms.functional import yes_or_no
from autograms import autograms_function

#this decorator allows the function to have special behavior such as temporarily returning replies
@autograms_function()
def chatbot():

    #model goes first here, we have a fixed introductory message. Pauses program and returns a reply
    reply("Would you like me to tell you more about the latest advances in AI?", ADDRESS="ask_question")
    #program will continue from this point after first user reply 

    #The agent decides whether it thinks the user wants to talk about AI based on their response  
    user_wants_ai = yes_or_no("does the user want to talk about AI?")

    if user_wants_ai:
        #pause and save program and return a reply based on instruction below    
        reply_instruction(
            "Tell the user about the latest advances in AI. Mention that "
            "a new framework called AutoGRAMS was recently released that allows greater control over AI agents.",
            ADDRESS="tell_about_ai"
        )
        #continue program here after user response

    else:
         #pause and save program and return a reply based on instruction below  
        reply_instruction(
            "Confirm with the user what they would prefer to talk about.",
            ADDRESS="ask_preference"
        )
        #continue program here after user response

    #infinite while loop continues conversation as long as user keeps responding
    while True:
        #pause and save program and output reply based on instruction below
        reply_instruction("Respond to the user.", ADDRESS="continue_conversation")
        #continue program here after user response
```




### Restrictions
While `@autograms_function` supports various control flow constructs, it may not handle resumption within certain node types (e.g., `try`-`except`, `finally`). Ensure that `ADDRESS` labels and pauses occur within supported contexts like loops and conditionals.

## `@autograms_external()`

`@autograms_external()` is meant to allow for functions that interact with user specific memory of the program to be called from outside of the normal conversation chain. The are mainly used to interact with user specific global variables


## example use
```python
@autograms_external()
def update_user_settings(user_command):

   thought(f" The user made this request {user_command}. Should we change the chat_style setting? it is currently set to {user_globals['chat_style']}, and the options are {','.join(chat_styles)}")

   idx =multiple_choice("what should the chat style be set to?",chat_styles) 

   user_globals['chat_style'] = chat_styles[idx]

```

And then in the Autogram object wrapping the module, you can do
```python
autogram.apply(memory_object = memory_object,function=update_user_settings,user_command=user_command)
```

@autograms_external functions do not permanently modify the stack in the memory_object, are mainly used to change the UserGlobals object for user specific global variables defined in the module if there is one. 





## @autograms_node

Decorator for defining addressable nodes in Autograms. These nodes can serve as targets for `GOTO` and `RETURNTO` statements, enabling dynamic control flow within a function. They can also be used for logging and visualization purposes for showing graphs of the program, even if used without `GOTO` or `RETURNTO`.
### Behavior

- Allows the function to be a target for `GOTO` and `RETURNTO` statements.
- When an `ADDRESS` is provided, the function call is logged and can be revisited.


### Example usage

The following uses an autograms node combined with GOTO to design a chatbot that always replies with the next number of the Fibonacci sequence
```
from autograms import autograms_node,autograms_function
from autograms.functional import GOTO, reply

@autograms_node
def reply_value(value,ADDRESS=None):
    #pauses program to reply
    reply(f"value is now {value}")

@autograms_function():
def fibonacci():
   x=1
   reply_value(x)

   x_last=x


   reply_value(x+x_last,ADDRESS="output_x")
   x_last=x
   x = x+x_last

   #facilitates loop  by going to previous line with `reply_value(x+x_last,ADDRESS="output_x")`
   GOTO(destination="output_x")
   
```


