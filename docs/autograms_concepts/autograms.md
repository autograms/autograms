# How an autogram works

An autogram is defined by a an object of type Autogram. An autogram stores a collection of nodes as an OrderedDict type that form a graph that will define how the program is executed. Autograms can either be executed by the autogram.reply() or autogram.apply_fn() method. autogram.reply() is meant to get a reply from a chatbot, and autogram.apply_fn() is meant to call a specific module within the autogram and return a result, and can be used for non-conversational autograms.

## initializing the autogram

```
from autograms import Autogram, AutogramConfig, AutogramCompiler, read_autogram
```


Setting the arguments of the autogram config can control what chatbot model is used, to what prompt templates are used, to what python functions/imports are visible. An empty initialization gives the default settings, but to learn more about the options, see the section on autogram configs.
```
config = AutogramConfig()

```

To initialize the autogram from a spreadsheet, use the following code to read the spreadsheet from a csv, get the pandas dataframe, and initialize the autogram from a data frame

```
autogram = Autogram(autogram_config,df=df)
```
To initialize the autogram from AutoGRAMS compiled from python
```
with f=open(autogram_file):
    code = f.read()
autogram = AutogramCompiler(code,autogram_config)

```


To initialize the autogram directly in python, use the autogram.add_node() method to add nodes one at a time.

```
autogram = Autogram(autogram_config)
#very simple autogram that has 1 chat node that transitions to itself
autogram.add_node(name="node1",action="chat",instruction="respond to the user with prompt xyz",transitions=["node1])
autogram.allow_incomplete=False
autogram.update_autogram()
```

Lastly, autograms coded in a separate file (.py or .csv) can be initialized using the read_autogram method. For instance, 


```
autogram = read_autogram(autogram_file)
```







## getting replies
when calling autogram.reply() with no arguments, the program starts from either the first node in it's ordered dict, or a node with the name "start1" if any such node is defined. At each iteration of the main loop of the program, autogram executes an instruction associated with each node, and applies transition behavior defined by each node. It does this until it hits a chat type node, in which case it will return a reply, along with the current state of the program, defined by the memory object. So let's say at the first turn we call

```
autogram_reply,memory_object = autogram.reply()
user_reply = input("agent: " +autogram_reply+"\nuser: ")
```
And we will wait for the user reply. We can get the second reply from the model by calling 
```
autogram_reply,memory_object = autogram.reply(user_reply,memory_object)
```
The memory object keeps track of where we left off, so this time when we call `autogram.reply(user_reply,memory_object)`, the program will start by applying the transition behavior of the chat node at which the previously reply came from. It will then continue it's loop until it reaches another node of chat type, at which point it will return the autogram's reply and updated memory object. Since the entire state of the program is defined in the memory object, this allows programs to be saved and loaded later--for instance, using jsonpickle

```
import jsonpickle
encoded= jsonpickle.encode(memory_object)
with file = open("memory.json",'w'):
    file.write(encoded) 

with file = open("memory.json"):
    new_memory = file.read(encoded) 

```

Would allow us to continue an old conversation. This feature is especially useful for chat APIs where it is often necessary save and load the state of the conversation to a database.



## Nodes

The behavior of an autogram is defined by nodes--where each node executes an instruction and applies a transition to another node. Each node has a series of fields that define it's behavior. We will give a more comprehensive overview of all the fields that a node has later, but will give an introduction here. A Node has a name, an action, and instruction, and a list of potential transitions. 

For instance, a node that asks the user if they would like to solve a math problem, and goes to a node called "ask_math_problem" if they say yes or a different node that says "ask_user_preference" if they say no could look like this.


```
exec_node(name="ask_math",transitions=["ask_math_problem","ask_user_pref"],action="chat","instruction"="ask user if they would like to try solving math problem",transition_question="Would the user like to solve a math problem?",transition_choices=["yes","no"])
```


A nodes behavior is governed by it's [action](actions.md), [instruction](#instruction), and [transitions](transitions.md)
## Transitions


There are several ways to have transitions in the AutoGRAMS. The most commonly used transitions for chatbots are transitions predicted by the autogram's classifier, you need to initialize a node with a list of transitions, a transition question, and a list of transition answers with a one to one correspondence to the transitions. For instance 

```
exec_node(name="ask_math_problem",
    transitions=["answer_correct","answer_incorrect","asked_question","user_not_sure"],
    action="chat","instruction"="Make up an simple algebra problem for the user to solve, and include this in your reply.",
    transition_question="What did the user do?",
    transition_choices=["gave a correct answer","gave an incorrect answer","asked a question","wasn't sure where to start"])
```

In this case, there are 4 possible transitions, and 4 corresponding transition choices. The classifier chooses which transition choice most applies based on the user response, and this decides the transition. 


There are other types of transitions that are described in the main article on [transitions](transitions.md). This includes `.*` and `.n` transitions, which can be used to implement traditional conditions (if else statements) as well as other types of rule based behavior. Using special transition nodes can break down complex transition questions into a series of simpler ones. (Interjection nodes)[interjection.md] allow for certain nodes to be reachable after any conversational turn, and can be useful for unexpected user behavior. Lastly, while this feature is still experimental and not fully tested, it is possible to have dynamic transitions that use a [variable](variables) as a transition, allowing the graph to be modified during the execution of the program.







## Instructions

Instructions execute the main operation of the node. The way an instruction is interpreted varies depending on the action of the node. The main actions at a high level are:

1. Chat ("chat","chat_exact","chat_suffix") Write a response to the user. The instruction tells the model how to respond.
2. Thought ("thought","thought_exact","thought_qa") Write a response internally. In this case, an instruction tells the model what to think
3. Transition ("transition") - node that does not execute instruction but allows for additional branching 
4. function ("function","local_function","global_function") A node that calls another AutoGRAMS function and gets result. the action is an AutoGRAMS function. When coding in AutoGRAMS compiled from python, you have the option to call the function directly which creates a node with a function calling instruction implicitly
5. Python function ("python_function") - used to call a python statement, function, or api. In this case the instruction is python code.  When coding in AutoGRAMS compiled from python, you have the option to write the python code directly which creates a node with a python instruction implicitly
6. prompt setting ("set_prompt","set_user_prompt","append_prompt","append_user_prompt"). These actions modify  the starting prompt of the model. The instruction specifies the new prompt or addition to the prompt depending on the specific action type.


It is possible to embed [variables](#variables) in instructions so the exact instruction depends on a previous model or API output. 

See the [actions](actions.md) documentation for a more detailed overview.







## Internal functions and scopes

Nodes in an autogram can be made callable--which allows them to be called within an autogram or directly from python using the autogram.apply_fn() method. Nodes that are callable must have a name defined with "()" and any arguments the node expects.

AutoGRAMS functions are sub graphs that execute and return a result. When a function is called, the autogram temporarily jumps to a callable node, and it propagates though the graph until a special `return` transition is encountered. Functions allow for graph modules to be reused. For instance, consider an AI tutor autogram with the following graph:

<iframe src="/images/chat_fun.png" max-width="100%" height="540px" width="100%"></iframe>

The graph contains a subgraph that asks the user a question to quiz them. This routine could be called from different branches of the conversation tree, and always returns to the node that calls it when it hits a special return transition. This allows subgraphs to be reused at multiple points in an autogram. 


AutoGRAMS functions also allow for the scope of the conversational history to be better controlled--for instance, if you'd like to compute something using a multiple reasoning steps, but then hide the intermediate steps of the reasoning from the prompt once it is finished executing, AutoGRAMS functions allow you to do this. 








See the main documentation of [AutoGRAMS functions](actions.md#function-actions) for a full overview. 

## calling AutoGRAMS functions from python

AutoGRAMS functions can be called both from within an autogram and externally from python. The AutoGRAMS apply_fn() for calling AutoGRAMS modules from python accepts the following arguments:

`entry_node` (required) - name of callable node that begins the function
`args_list` (required)  - list of the python variables that will be passed as arguments to the module
`memory_object` - Memory object to initialize the function call with. Defaults to `None`, generally isn't needed for local functions
`memory_dict`- dictionary representation of memory object, defaults to `None`
`function_type` - type of AutoGRAMS function to call as, defaults to "local"



## Python functions


Python functions are calls to python code, functions, or apis, using the python interpreter to interpret the statement. The arguments passed to the [Autogram config](autogram_configs.md) determines what python functions are available and in scope. Python functions can also return variables of any type. 


See the main documentation of [python functions](actions.md#python-actions) for a full overview.


## Variables

Variables in AutoGRAMS can be any python object. Variables are set when AutoGRAMS instructions are executed. To define a variable, include an equals sign in the instruction to assign the output of the node to the variable. For instance:
```
exec_node(action="thought",instruction="summary=Write down a summary of the conversation so far.")
```
Will execute an internal dialogue where the model will respond to the instruction, and save the resulting model output into the variable `summary`. In AutoGRAMS compiled from python, it's also possible to use regular assignments outside of the instruction:
```
summary=exec_node(action="thought",instruction="Write down a summary of the conversation so far.")
```
And the AutoGRAMS compiler will infer the correct instruction syntax to cause the variable assignment to be executed.  Variables can be used in 2 ways--by passing them in python function nodes, or by incorporating them as a string into an instruction (which could be for any node type). To use a variable in a python function, you simply use the variable as you would in any python statement. for instance `summary_str='here is a summary: '+summary` (or equivalently `exec_node(action="python_function",instruction="summary_str='here is a summary:' +summary"`) will result in a string that concatenates the prefix 'here is a summary:' with the summary string output by the model at the previous node. 

The second way to incorporate the variable is the the syntax `$summary`, which results in an instruction that is dynamically formed based on the value of the summary when the node is assigned. this syntax only works for python strings, or other python objects that have the `__str__` method to be converted to strings. This is mainly used for chat and thought type nodes that are passed to the model. For instance, later in the conversation we might use a node like this:


```
exec_node(action="chat",instruction="Respond to the user. Based on a summary of the conversation so far $summary, relate your reply to the user with something you've talked about previously" )
```

Note that depending on your application, it may be unadvisable to use $ syntax in python_function nodes since this could be used to inject code or result in errors. So for instance, if you used the statement `exec_node(action="python_function",instruction="'here is a summary:' + $summary"`, it would set the value of summary in the instruction string before executing it as a python statement. This would result in an error because summary is not wrapped in quotes.

There is an additional way to use the $syntax, which is to include brackets around where the variable is used, which omits this portion of the instruction if one or more variables is undefined.

So for instance the instruction in

```
exec_node(action="chat",instruction="Respond to the user.{Based on a summary of the conversation so far $summary, relate your reply to the user with something you've talked about previously}" )
```
Will omit the bracket text and simply be "Respond to the user." if the summary variable hasn't been set.





## Memory Object

The AutoGRAMS memory object stores everything associated with a specific run of the program. The two main components are the function stack, and model turns (optional, mainly used for logging model inputs/outputs). Each layer of the memory stack stores the chatbots conversation turns, as well as any variables set at that layer of the stack. The memory object can be saved and reloaded using jsonpickle to save and load the state of a program or chatbot. 

```
autogram_reply,memory_object = autogram.reply(user_reply,memory_object)

```

`memory_object.memory_dict['stack']` - contains the state of the program. It is represented as a list that starts of with length one when a program is initialized. It is appended by one everytime a function is called, and the top element is deleted everytime a function returns. `memory_object.memory_dict['stack'][i]` represents the ith innermost scope level of the program

`memory_object.memory_dict['model_turns']` - list that contains information about every turn that was processed by the chatbot or classifier, including enough information to recover the prompt, as well as the model's response or prediction. Each element of the list is a dictionary, with the 'model' field specifying whether it is a chatbot turn (that executes an instruction) or a classifier turn (that predicts a transition)

Some useful methods are 

`memmory_object.get_variable_dict()` -- returns the variables currently in scope for the top level of the stack. 
`memmory_object.get_last_state()` -- returns the most recent state of the program 



