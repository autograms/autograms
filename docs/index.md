# AutoGRAMS language

This is the official documentation of the [AutoGRAMS framework](https://github.com/benkrause/autograms). AutoGRAMS, or autonomous graphical agent modeling software, is an agent framework and a high level programming language that combines machine instructions with language instructions, and supports concepts such as function calls and memory within the language. AutoGRAMS programs, which we refer to as autograms, are represented as graphs, allowing users to easily program tree or graph networks of prompts into chatbots. The long term vision of AutoGRAMS is to become the language that AI uses to program AI. This section includes the introduction and guide to getting started.


## Introduction

While the AutoGRAMS framework can be used as a complex programming language, the initial motivation and applications were relatively simple. Often LLM model's struggle to lead conversations that require multiple conversational steps that can take several trajectories. Let's say you want an LLM to teach someone something or interview a person about a topic. If you simply give the model a prompt at the start, it will do pretty well for the first turn. However, if you try to get it to follow a complex script, it will often veer off from this, and just go wherever the user takes the conversation. While being more reactive to the user can be useful, the ability to proactively lead a conversation according to a script or series of steps is also important. One way to better control this is to design a tree or graph of instructions for the model, instead of simply having a prompt at the start. The idea is that the model starts off with a single instruction, but depending on how the user responds, the instruction that the model receives at the next turn will be different. AutoGRAMS allows you to consider the tree of possible situations that an agent might encounter, and preprogram an instruction for each of those situations. This works by defining a graph using a spreadsheet (or in python if you prefer), where each row of the spreadsheet is a node in the graph.  

Let's consider an example of how this can work. Let's say we want the model to act as a recruiter and asks the user their salary expectations. After receiving the user's reply, the agent must chose which of potentially several nodes it should transition to next. To do this, it can use a predefined multiple choice question such as 

Which is the following did the user do?


A. The user asked a question

B. The user avoided the question or said they weren't sure

C. The user gave a salary range

We can then use a language model to predict, based on the user's response, whether the answer should be A, B, or C. Then, the agent can jump to a different predefined node depending on which answer the agent predicted. This allows for instructions to be given to the model situationally, allowing for more complex multi-turn instructions to be executed. 

![image](agent_graphs/recruiter_chatbot/ask_salary.png)



For many users, the above usecase of designing trees or graphs of situational instructions may be the main usecase of AutoGRAMS. However, after implementing this basic functionality, we realized the utility of giving this type of framework more flexibility. So we decided to develop a full programming language that uses variables, memory, functions (even recursion), and external python calls, built around this idea of AI agents as graphs. 



## AutoGRAMS as a programming language

When computer programs run, they execute instructions and facilitate the transitions (loops, conditionals, sequential statements etc.) between these instructions. A programming language in the traditional sense executes exact instructions and facilitates transitions that use exact boolean logic. However, for many complex applications, executing exact instructions can be intractable since it requires writing logic to describe any situation. Generative language models have developed the ability to follow complex human language instructions such as "Write a paragraph about X" or "write code the does Y" that would be intractable to implement using the basic logical instructions of a programming language. One of our main goals with AutoGRAMS was to develop a programming language that allows for execution of both traditional machine instructions as well as human language instructions as primitive operations in the programming language, as well as to use both traditional boolean logic and language model predictions to facilitate the transition between instructions in a program.

In AutoGRAMS, each program or function is represented as set of nodes with behaviors defined in each respective node's fields. AutoGRAMS represents each autogram as a graph--each node executes an instruction, and facilitates a transition to another node that it connects to. Loops can be implemented with into these graphs by having the graph circle back on itself, and by ensuring that there is a transition in the loop that exits that graph if the right conditions are met. AutoGRAMS also supports some basic python statements as well as any predefined python function call that is passed to the agent at initialization. This mechanism allows for external API calls. Variables in AutoGRAMS are allowed to be any python object--calls to the chatbot yield string variables, whereas calls to python statements or functions can potentially be any object. These variables can then be used in later instructions, or passed into other external python functions.

We also implement function calls within AutoGRAMS, where the calling node jumps to another graph, and that graph is traversed until it hits a special return node, which returns a result back to the calling node. These graph functions can also call themselves recursively, allowing for recursive logic to be built around an LLMs instruction following capabilities. There are several different kinds of functions in AutoGRAMS, which have different rules about variable scope, which is maintained using a function stack.

## Installation

You can install with `pip install .` in the top level directory. Officially supports python 3.9 but may work in other versions. Will require setting up CUDA toolkit and pytorch to run the huggingface models.



## Writing the code

As we mentioned before, programs in AutoGRAMS are represented as a list of nodes, each which contain a series of fields. There are several ways to program these nodes. If you'd like to get started quickly, coding in a spreadsheet or coding directly in python may seem more familiar. If you'd like to code very advanced programs, AutoGRAMS compiled from python allows for more advanced features like combining interconnected nodes with standard python code and loops, although these more advanced features aren't neccessary to use it.

1. code in a spreadsheet


Spreadsheets are potentially useful since most programs in AutoGRAMS consist mainly of string fields such as instructions, questions, and answers, and defining each node as a row in a spreadsheet, and each field as a cell in a spreadsheet, could be convenient for this. Describing the tree of a simple chatbot is fairly straightforward spreadsheet--you need to define the node names in one column and comma separated transitions in another field. However, Spreadsheets are less convenient for programs that more closely resemble traditional programs. For instance, programs that use loops can be coded in a spreadsheet by having a graph loop back on itself,but this probably isn't ideal. 


2. code directly in python

Another way to program nodes it to just define them add them one by one to to the agent. This might be most straightforward if you'd like to code in simple python. Some of the downsides to this downsides are similar to coding in a spreadsheet--since the program is defined by the graph, adding features such as forloops need to be implemented in the graph. Also, if you'd like your AutoGRAMS program to mix in python statements or variable assignments, these need to be passed as strings in the instruction field of the node rather than 

3. AutoGRAMS compiled from python

This third approach gives the flexibility of writing code--including loops, python statements, and variable assignments, directly in python, while also mixing in AutoGRAMS graph nodes. The .py file is read and compiled into an AutoGRAMS graph automatically--So for instance if you write a forloop around an AutoGRAMS node, the AutoGRAMS compiler will make new nodes automatically to handle the forloop and the resulting AutoGRAMS graph will loop back on itself. 



We will start with a simple example. Let's say we have an agent that offers to tell the user about recent advances in AI. If the user wants this, it continues with this. Otherwise it asks the user what they would prefer to talk about.


<iframe src="agent_graphs/simple_chatbot/full_graph.html" width="100%" height="300px"></iframe>
Click on a node in the graph above to view fields.





### Coding nodes in a spreadsheet

We will use the spreadsheet to define 4 nodes, where each row in the spreadsheet defines a node. Generally, the first node will be the first row, although if name a node "start1" then this will automatically be set to the first node. In the case below, the first node gives an `instruction` to tell the user "Would you like me to tell you more about the latest advances in AI?", as listed in the instruction field. We name the node "ask_question". 


<iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vSgcJiEpGXvXcxCppisqXtx2PAyBrj28_tJKeIUf_Thi1IR_YG4Wg3lfwlQWqSWNrUZ53YBScZmjM3P/pubhtml?gid=0&amp;single=true&amp;widget=true&amp;headers=false" width="100%" height="300px"></iframe>

You can name nodes whatever you want, but chosing meaningful names can help because 
1. you need to reference these names in transitions to connect nodes 
2. The node names show up when you do visualizations of the graph

The action field defines the action that is performed in a node, which also defines what type of node it is. A `chat_exact` node tells the agent to reply with the exact text that it in the instruction, and does not actually call the underlying chatbot language model. These types of nodes are often useful for introducing agents on the first conversation turn. The rest of the nodes are `chat` nodes, Where the model is told to follow the instruction to reply to the user, which calls the chatbot language model.

The way this agent moves through the graph will be dependent on the user's answer, and is defined by the transitions, transition question, and transition choices. The "transitions" column expects a comma separated list of nodes that the agent can transition to next. For nodes that allow for multiple transitions, the order of the transitions matters, since they need to be aligned with the transition choices. In the node `ask_question`, there are 2 transitions defined-- `tell_about_ai` and `ask_user_preference`. There is also a transition question--`Does the user want to talk about ai?` and 2 transition answers, `transition choice a`, which is `yes`, and `transition choice b`, which is `no`. The way that these nodes works is:

1. agent executes the instruction, in this case, replying with the exact text "Would you like me to tell you more about the latest advances in AI?"
2. The agent waits for a response, in this case, the user reply
3. The same node then asks the classifier (Which is also a language model) the `transition question`:`Does the user want to talk about ai?`
4. The classifier predicts an answer-the agent limit the predictions of the classifier to just `yes` and `no`for yes/no questions, and 'A-Z' for non yes/no multiple choice questions.
5. the answer is used to pick the transition. Since `yes` is the first answer, if the answer to the question is predicted to be yes, the agent will transition to `tell_about_ai`. Otherwise it will transition to `ask_user_preference`

For nodes with only one transition, steps 3-5 are skipped since the transition is deterministic. Therefore, no transition question or choices are needed. The final state of the chatbot, `continue_conversation`, connects to itself, allowing the conversation to continue indefintely. 




### Coding nodes in python directly

Nodes can be coded in python directly by adding them to an autogram object one by one. While this is technically the pure python way of coding, it allows less flexibility. 

```
from autograms import autogram
```

To add nodes, use the `autogram.add_node()` method to add them one by one. This is equivalent to a row in the spreadsheet.

This first block initializes the "ask_question" node as a "chat_exact" node. The fields are the same as the spreadsheet, except that fields associated with transitions are initialized as lists. For instance, transitions is a comma separated list in the spreadsheet. Instead of having separate fields for each transition choice (`transition_choice_a`, `transition_choice_b`, ..., etc.), `transition_choices` is defined in a list that is the same length as `transitions`. For a full list of arguments to add_node, see the documentation of the `__init__` method of BaseNode `nodes/base_node.py`, which is where these arguments are ultimately passed. The fields of the spreadsheet are ultimately converted to arguments of this format. 


```

autogram.add_node(
      action = "chat_exact",
      name = "ask_question",
      transitions = ['tell_about_ai', 'ask_user_preference'],
      instruction = "Would you like me to tell you more about the latest advances in AI?",
      transition_question = "Does the user want to talk about ai?",
      transition_choices = ['yes', 'no'],
      )
```

This next blocks initializes the remaining nodes in the above example. No `transition_question` or `transition_choices` are needed since there is only one possible transition for each of those nodes.

```

autogram.add_node(
      action = "chat",
      name = "tell_about_ai",
      transitions = ['continue_conversation'],
      instruction = "Tell the user more about the latest advances in AI.",
      )

autogram.add_node(
      action = "chat",
      name = "ask_user_preference",
      transitions = ['continue_conversation'],
      instruction = "Confirm with the user the user what they would prefer to talk about.",
      )

autogram.add_node(
      action = "chat",
      name = "continue_conversation",
      transitions = ['continue_conversation'],
      instruction = "Respond to the user.",
      )
```


### compiling AutoGRAMS from python

In order to allow python code, loops, and conditionals to be directly implemented in combination with AutoGRAMS nodes, we created a compiler that converts python code into AutoGRAMS graph, allowing python code and AutoGRAMS nodes to be interleaved. This code is not true python, but behaves identically for simple python programs in most cases, other than the AutoGRAMS nodes which behave differently. The idea is that pure python statements and external function calls are treated as special "python_function" nodes that call the python interpreter, and loops and conditionals can be used to form an AutoGRAMS graph automatically. Each (non-python) AutoGRAMS node is implemented using a special built in method called exec_node(), which takes the same arguments as autogram.add_node(). The main difference is that in compiled AutoGRAMS, the order of nodes can be used to infer transitions. If nodes do not have transitions, nodes are executed in the order they appear in the code. nodes can also use a special "next" transition that simply goes to the next node or line of code. The first 3 nodes of the simple program can be implemented as follows:

```
#notice the "next" transition, which will go to "tell_about_ai" since it is next in the code.
exec_node(
      action = "chat_exact",
      name = "ask_question",
      transitions = ['next', 'ask_user_preference'],
      instruction = "Would you like me to tell you more about the latest advances in AI?",
      transition_question = "Does the user want to talk about ai?",
      transition_choices = ['yes', 'no'],
      )
exec_node(
      action = "chat",
      name = "tell_about_ai",
      transitions = ['continue_conversation'],
      instruction = "Tell the user more about the latest advances in AI.",
      )

exec_node(
      action = "chat",
      name = "ask_user_preference",
      transitions = ['continue_conversation'],
      instruction = "Confirm with the user the user what they would prefer to talk about.",
      )

The last node, which connects to itself to allow the conversation to continue indefinitely can be implemented in 2 different ways--one using an explicitly defined transition back to itself

```
exec_node(
      action = "chat",
      name = "continue_conversation",
      transitions = ['continue_conversation'],
      instruction = "Respond to the user.",
      )
```

And the other using an infinite while loop to make the sample transition implicitly

```
while True:
      exec_node(
            action = "chat",
            name = "continue_conversation",
            instruction = "Respond to the user.",
            )
```

Using the while loop will result in a slightly different representation in the AutoGRAMS graph since extra nodes will handle the while loop logic, however this is functionally equivalent to using the self-transition. Note that since this is a chat node, the loop will temporarily pause each time to get the user's response, but you probably wouldn't want to have an infinite loop of non-chat nodes. 



## Visualizing the agent




Since AutoGRAMS programs are defined by nodes, visualizing programs in AutoGRAMS can be very helpful for understanding how they work. The `make_interactive_graph.py` script in the highest level of the repository can generate interactive graphs for any AutoGRAMS agent coded in a spreadsheet or in python. To generate the graph for the above example, you can run

python ``make_interactive_graph.py --autogram_file agents/tutorials/simple_chatbot.csv``

or alternatively ``make_interactive_graph.py --autogram_file agents/tutorials/simple_chatbot.py``

This will create several new files in a new folder `agent_graphs/simple_chatbot`.
Potentially most useful full be `agent_graphs/simple_chatbot/full_graph.html`. This file can be opened in a browser to view an interactive visualization of the agent. You can click on any node to highlight it and view the fields for that node.

Here is a full list of the arguments for `make_interactive_graph.py`

`--autogram_file` - the path of a .csv or .py file where your agent is coded
`--filter_category` - only graph nodes defined by `State Category` and their transitions. `State Category` is a node field that you can use to categorize nodes. This allows for partial graphs of complex programs to be used. the output files will be named after that state category instead of `full_graph` if this argument is used.
`--label_by_inst` instead of using node names to label nodes, use an abbreviation of the node instruction.
`--graph_format` for the graph image file, what image format should be saved (png, pdf, etc.)
--read_from_pure_python - if passing in a .py file, this tells us whether it is AutoGRAMS compiled from python (default) or AutoGRAMS implemented in pure python.



## Running a chatbot

You can use `run_autogram.py` to run a chatbot in the terminal. You need an agent file and an api key file if using any APIs. By default AutoGRAMS does use the open AI API for chatbots, but you can also use huggingface LMs that run locally if you specify this in the agent config. You can copy paste your open ai API key into the appropriate slot in api_keys.json, or define a similar json file somewhere else with "openai" as a key and the actual key as the value.


To run the tutorial example above, you can run:
`python run_autogram.py --autogram_file agents/tutorials/simple_chatbot.csv --api_key_file api_keys.json --interactive`

This will create an interactive chatbot in the terminal where you can chat with the agent.