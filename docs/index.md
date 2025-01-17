---

title: Home

---

# AutoGRAMS

Welcome to the official documentation for [AutoGRAMS](https://github.com/autograms/autograms), the Autonomous Graphical Agent Modeling Software. AutoGRAMS is a Python framework designed to transform chatbots into dynamic, stateful programs. It leverages Python’s full power, allowing developers to craft intelligent conversational agents with advanced control over dialogue flow, memory, and program state. 


By representing a chatbot as a continuously running program, AutoGRAMS enables you to precisely control the prompts and memory at different points in the conversation. Decisions made during conversations directly influence the program’s execution path, variables persist as the chatbot’s memory, and conversations seamlessly adapt based on the program’s current state.



## Introduction

Modern conversational AI systems often face challenges in guiding users through structured, multi-turn interactions. For instance, an educational tutor chatbot may need to follow a defined script or dynamically adjust its path based on user input. Similarly, a virtual recruiter might want to branch into different conversational routes depending on the user's qualifications. Standard AI models often lose coherence in such scenarios, struggling to maintain both the context and structure of a conversation over time.

AutoGRAMS addresses these challenges by treating chatbots as dynamic programs. Conversations are implicitly modeled as graphs, with each node representing a specific conversational state and transitions between nodes representing the dialogue flow. This approach unlocks a range of powerful features that make AutoGRAMS uniquely suited for building complex, stateful agents:

---


### Key Features

1. **Continuously Running Programs**  
   AutoGRAMS enables you to write chatbots as Python programs that persist their state across user interactions. When using the `@autograms_function` decorator, the chatbot resumes execution exactly where it left off after each conversational exchange with the user, allowing for highly dynamic, context-aware conversations.

2. **Save and Resume Program State**  
   AutoGRAMS allows you to serialize the program’s complete state, including the call stack, local and global variables, and control flow position. This means you can pause the program after any conversational turn, save it, and later reload it to continue from the exact same state.

3. **Dynamic Control Flow**  
   AutoGRAMS introduces constructs like `GOTO`, `TRANSITION`, and `RETURNTO` to enable flexible navigation through your chatbot’s logic. These are used to jump to special autograms nodes that you define with addresses.

4. **AI-Driven Decisions**  
   Integrate LLM-powered decision-making directly into your chatbot’s workflow. Functions like `yes_or_no` and `multiple_choice` guide the program’s branching logic based on user input or internal criteria, enabling intelligent and dynamic conversation flow.

5. **Memory Management**  
   AutoGRAMS automatically manages memory across turns, preserving variables and conversation history. The memory object tracks context, ensuring smooth continuity and coherence in multi-turn dialogues.

6. **Visualize Conversation Flow**  
   AutoGRAMS can compile your chatbot’s logic into detailed graph visualizations. These visualizations map out the program’s states and decision points, helping you design, debug, and understand the flow of your conversations at a glance.

---

## How AutoGRAMS Works

At its core, AutoGRAMS reimagines chatbots as programs that can be paused, serialized, and resumed. Each conversation is a journey through the program's logic, with the chatbot's state representing its memory and the current position in the program determining its next actions. Here’s how it comes together:

- **Pause and Resume**: Whenever the chatbot provides a reply, AutoGRAMS pauses the program execution. The current state is saved, and the program can be reloaded later to continue seamlessly from the same point.
  
- **Dynamic Graph Representation**: Conversations are represented as a graph of nodes (states) and edges (transitions). AutoGRAMS allows precise navigation of this graph using dynamic constructs like `GOTO`.

- **LLM-Powered Decisions**: By embedding decision-making functions directly into the program, AutoGRAMS ensures that the chatbot’s actions align with its conversational objectives, guided by both user input and AI-driven logic.

Together, these capabilities enable a new level of flexibility and control in chatbot development, making AutoGRAMS the ideal framework for building advanced conversational agents.

---


Welcome to the official documentation of the [AutoGRAMS framework](https://github.com/autograms/autograms). AutoGRAMS, or Autonomous Graphical Agent Modeling Software, is a Python library designed to streamline the creation of intelligent, stateful chatbots. It builds on the concept of conversational agents as dynamic systems with complex state management, providing powerful tools to craft flexible, controlled dialogues. Unlike its earlier version, which introduced a custom programming language, this new iteration leverages pure Python for maximum flexibility, integration, and ease of use.

## Introduction

Modern conversational AI systems often struggle to lead multi-turn conversations along specific paths or adhere to structured scripts. For example, imagine building an educational chatbot or a virtual recruiter. You may want the agent to guide the user through a carefully planned sequence of interactions. However, standard language models tend to lose focus over long conversations or struggle to maintain a predefined conversational structure. 

AutoGRAMS solves this problem by allowing you to define these structured interactions directly in Python. It offers tools to build chatbot workflows using common programming constructs like loops, conditionals, and stateful branching. Conversations are implicitly represented as a dynamic graph, where each node corresponds to a specific point in the conversation. Here's what makes AutoGRAMS unique:

### Key Features

1. **Stateful Conversations with Serialization**  
   AutoGRAMS allows chatbots to save and restore their entire program state between turns, enabling mid-conversation reloads. By using the `@autograms_function` decorator, functions can automatically handle program state, allowing the chatbot to seamlessly continue from the exact point it left off after each reply.

2. **Automatic Conversation History and Prompt Management**  
   Every reply in AutoGRAMS is generated within a memory context that tracks conversation history, manages system prompts, and seamlessly integrates new user inputs. This memory is thread-specific and ensures isolation between concurrent sessions.

3. **Decision-Making Functions**  
   AutoGRAMS offers specialized functions like `yes_or_no` and `multiple_choice`, designed to streamline branching logic. These functions allow the chatbot to make decisions based on user input or internal criteria and adjust the conversation flow accordingly.

4. **Advanced Control Flow (GOTO and RETURNTO)**  
   For more complex chatbot behaviors, AutoGRAMS introduces control flow constructs like `GOTO` and `RETURNTO`, enabling precise navigation across conversation states. These constructs are especially useful for state-driven chatbots that require jumping between different points in a workflow.

5. **Integration with AI APIs**  
   AutoGRAMS simplifies calling AI APIs (e.g., OpenAI) to handle tasks like text generation, classification, and embedding extraction. These functions are designed to work seamlessly with the memory and state management system.



## Installation and Requirements

You can install AutoGRAMS via pip, either with 


```
pip install autograms
```

or `pip install .` from the root directory

Requirements:
- **Python 3.9+**
- **Graphviz** (optionial, for visualizing conversation graphs). On Linux:
  ```
  sudo apt install graphviz
  ```
- **OpenAI API Key** (optional, for openai api--can also use other models through proxy). Set it in your environment:
  ```
  export OPENAI_API_KEY=[your_key]
  ```
  Alternatively, you can store API keys in an `api_keys.json` file for flexibility.

---



## Simple "getting started" example



Here we'll walk through setting up and running a basic chatbot using Autograms. The example chatbot prompts the user about their interest in AI and dynamically adjusts the conversation based on their response. We'll also generate an interactive graph to visualize the flow of the chatbot.




### Step 1: Coding a simple chatbot

Let's create a new file called `simple_example.py` to code a very simple autograms chatbot that asks the user if they would like to know more about the latest advances in AI, and tells them a bit about AutoGRAMS if they say yes.
```python
from autograms.nodes import reply, reply_instruction
from autograms.functional import yes_or_no
from autograms import autograms_function

#this decorator allows the function to have special control flow behavior such as temporarily returning replies
@autograms_function()
def chatbot():

    #model goes first here, we have a fixed introductory message
    reply("Would you like me to tell you more about the latest advances in AI?", ADDRESS="ask_question")
    #program will continue from this point after first user reply 

    #The agent decides whether it thinks the user wants to talk about AI based on their response  
    user_wants_ai = yes_or_no("does the user want to talk about AI?")

    if user_wants_ai:
        #pause and save program and output reply based on instruction below    
        reply_instruction(
            "Tell the user about the latest advances in AI. Mention that "
            "a new framework called AutoGRAMS was recently released that allows greater control over AI agents.",
            ADDRESS="tell_about_ai"
        )
        #continue program here after user response

    else:
        #pause and save program and output reply based on instruction below  
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

What's Happening Here?
1. `reply` and `reply_instruction`: These nodes prompt the user. They pause the program, send a reply, and wait for user input before resuming.

2. `yes_or_no`: This function decides the next flow based on an AI model's interpretation of user input. It’s not user-facing; instead, it processes the chatbot’s own decision.

3. `ADDRESS` Parameters: These labels allow the chatbot to jump to specific points (Advanced), enabling dynamic flow and mid-conversation updates, and can also be used to help visualize the program




When the chatbot hits a reply or reply_instruction, it sends the response and pauses, saving the full state and memory of the program to a serializable object that can be saved and reloaded. After the user replies, the program resumes from that point, maintaining context.

All of these nodes and function we are calling have access to a shared memory object, automatically logging the conversation and allowing prompts to be formed automatically, and managing the stack for each time we return.  

### Step 2
 
Next, create a script called `run_simple_example.py` to run the chatbot function. This script will use the `Autogram` class to manage memory and handle user interactions.
```python
from autograms import Autogram
from simple_example import chatbot

# Initialize the Autogram class with the chatbot function
autogram = Autogram(root_function=chatbot)

# Start the chatbot and capture the first reply
chat_reply, memory_object = autogram.reply()

# Loop to handle user interaction
while True:
    print(f"Agent: {chat_reply}")
    user_input = input("User: ")

    # Pass user input to the chatbot and get to the next pause point in our chatbot function (reply or reply_instruction)
    chat_reply, memory_object = autogram.reply(user_input, memory_object=memory_object)
```


use `python run_simple_example.py` to run the chatbot. 


Alternatively, from the root directory of the autograms repository, you can run your chatbot with:


```
python run_autogram.py --autogram_file path/to/simple_example.py
```


You can also quickly debug common problems in the chatbot with 


```
python run_debug_autogram.py --autogram_file path/to/simple_example.py
```

which will simulate many conversations with the user without calling any model APIs


### Step 3: visualize the code
create a new file called generate_graph.py
```python
from autograms.graph import compile_graph
from simple_example import chatbot

# Compile and save the graph for the chatbot
graph = compile_graph(chatbot)
graph.save_visualization(save_folder="simple_example_graph", graph_format="png")
```

and run `python generate_graph.py`

This will create two files:

PNG Image: A static graph visualization.
Interactive HTML graph: allows you to highlight nodes to see code.




## More examples and useful functions

See `run_autogram.py`, `debug_augogram.py`, and `visualize_autogram.py` for code that is useful for running, debugging, and visualizing autograms. Also see the `/examples` folder for more examples of autograms chatbots with comments








 

