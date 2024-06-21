

# Actions

Actions in AutoGRAMS can be set by using the "action" argument exec_node() or agent.add_node() method in python, or by setting a field of the spreadsheet called "action". Setting action effectively determines the type of the node and how the node's instruction will be interpreted. The main actions at a high level are

1. Chat ("chat","chat_exact","chat_suffix") Write a response to the user. 
2. Thought ("thought","thought_exact","thought_qa") Write a response internally
3. Transition ("transition") - node that does not execute instruction but allows for additional branching 
4. function ("function","local_function","global_function") A node that calls another AutoGRAMS function and gets result
5. Python function ("python_function") - used to call a python statement, function, or api
6. prompt setting ("set_prompt","set_user_prompt","append_prompt","append_user_prompt"). These actions modify  the starting prompt of the model


## Prompt Actions

Prompt actions are nodes that set or modify the starting prompt of the model. By default, starting prompts are set in the AgentConfig that is passed to the model, and prompt actions can be used to change this. Note that every 'local_function' and 'function' resets the starting prompt inside the function call, so if you'd like to change the starting prompt from the default inside function scopes you will need to use these actions.

### set_prompt

Sets starting prompt to be equal to instruction text

### set_user_prompt

Sets starting user prompt to be equal to instruction text. User prompts are not used in the actual model, and are only used during user simulations


### append_prompt

Appends starting prompt with instruction text

### append_user_prompt

Appends starting user prompt with instruction text. User prompts are not used in the actual model, and are only used during user simulations

## Chat Actions

Nodes with chat actions are points where the agent will respond to the user. At each chat style node, the agent.reply() method will return a result (the agent's reply to the user), along with the memory object that saved the state of the autogram so that the conversation can be continued.  

### chat

nodes with action set to "chat" pass the instruction to the model to get a reply. The instruction is interpreting as an instruction for how the model should reply. 

### chat_exact

in nodes with action set to chat_exact, the instruction is interpreted as the exact text the model should reply with. Chat exact nodes do not actually use the chatbot. These make the model's reply deterministic, unless the instruction contains a variable.


### chat_suffix

instructions in chat suffix nodes are interpreted as contain the exact reply that you want the chatbot to finish with. Instructions in chat suffix nodes are essentially converted to be "Reply to the user and finish your response with the text in instruction". chat_suffix nodes also use some special post processing to the models response--if the instruction is longer than the generation window for the model, there is an autocomplete feature that completes the response. There are also checks that regenerate the reply if the model fails to include the instruction at the end of it's response. If the model repeatedly fails to generate the instruction, the reply is set to the instruction exactly like in a chat exact node.



## Thought Actions

Thought actions are internal dialogue that the chatbot has with it's self. It can be used for chain of thought like mechanisms. You can control what thoughts are remembered in the conversation history and what thoughts are discarded using AutoGRAMS function calls. Thoughts are also useful for setting variables to build more complex programs.

### thought

The most basic thought action. A thought node gives and instruction to the model and get's a reply, which is used to update the internal dialogue 

### thought_qa

Similar to thought, but if you decide to store the result of the thought as a variable, it stores both the instruction and the thought. Can be useful for internal question answering where you may want to save what the question was too.

### thought_exact

A thought node where we essentially control exactly what the thought will be.

## Python actions

Python actions execute a python statement or call a python function. 

### python_function
nodes of action type "python_function" pass the instruction to the python interpreter, which interprets the instruction using the eval command. This allows python statements to be executed in an autogram.  Python functions can be set directly as nodes, for instance in pure python by using `agent.add_node(name="node1",action="python_function",instruction="sorted(list1)",transitions=["node2"]` would sort a list called list1 assuming that list was previously defined. The result could be achieved in a spreadsheet by setting the text in the action column to `python_function` and the instruction to `sorted(list1)`. When coding in AutoGRAMS compiled from python, you have a choice of defining an explicit node or just using a simple python statement. You can also omit the transitions and node names if you want the order of nodes to follow the order the code would be executed. So for instance, you could code the above example as

`exec_node(action="python_function",instruction="sorted(list1)")`

or more simply by just 

`sorted(list1)`

In the second example, the AutoGRAMS compiler would implicitly convert `sorted(list1)` into a python function node with an instruction equal to `"sorted(list1)"`, saving the user the work of doing this explicitly.



Depending on your application, you may want to avoid combining python_functions with `$` syntax for embedding variables into instructions of python_function nodes. If the variable embedded by the `$` set by the model or indirectly by the user, it could be used to inject arbitrary python code into the autogram. 

`exec_node(action="python_function",instruction="$variable1")`

While efforts have been made to make eval more secure by overriding potentially dangerous built ins, it would at the very least still be possible to inject code to overload the memory. For instance, if `variable1` were set to `"a"*(20**20)`, this would cause python would try to initialize an intractably large string. If you'd like to avoid this risk, avoid using $ variable embedding syntax in the instruction for python_function nodes, or if you must, make sure these variables are set very carefully (ideally with other python functions or chat exact nodes that are not derived from the user or model). Python nodes that were compiled directly from python statements do not pose this risk since they will not have variable code.

## Function actions

Function actions are when a node to call another AutoGRAMS graph and potentially gets a returned result. They are useful for reusing modules, and controlling the scopes of chains of thought. For instance, consider the following two scenarios. Lets assume there have been several conversational turns already.


Option 1.

```
# add earlier chat nodes here
# ...

summary = exec_node(action="thought",instruction="Write a summary of the conversation so far")

# add later chat nodes here
# ...
```



Option 2.

```
# add earlier chat nodes here
# ...

summary = get_summary()

# add later chat nodes here
# ...

@function
def get_summary():
  summary = exec_node(action="thought",instruction="Write a summary of the conversation so far.")
  return summary
```

In both option 1 and option 2, a variable called `summary` will be set to a string corresponding to the chatbot's predicted summary. However, in option 1, there will be a turn added to the conversation history corresponding to this instruction and thought. In option 2, this turn happens within the scope of a function, so it will be erased when the function returns. If going with option 2, the assumption is you would use $summary in any instructions or transitions where you want the model to consider the summary.

To better understand how functions are implemented as AutoGRAMS nodes, this is what the above code in option 2effectively becomes compiled as:

Option 2b

```
# add earlier chat nodes here
# ...

exec_node(action="function",instruction="summary=get_summary()")

# add later chat nodes here
# ...

exec_node(name="get_summary()",action="thought",instruction="instruction="Write a summary of the conversation so far.",transitions=["return"])

```

When implementing nodes directly in python or in a spreadsheet, you would need to add the fields as in the example above in option 2b. However, the AutoGRAMS compiler is able to read python like syntax and deduce this structure automatically.

There are 3 types of functions in AutoGRAMS all with different rules about scopes== "local_functions"-which have a local read and write scope, global_functions"-which have a global read and write scope, and regular "functions", which are a mix but mostly use a global read and a local write scope, meaning that they can see the past conversation turns but can't add to it permanently. 

When implementing a node using the exec_node() method, (or agent.add_node() in pure python, or as a row in a spread sheet), the action specifies the function type, so `action="function"`, `action="global_function"`, or `action="local_function"` can specify the function type. However in AutoGRAMS compiled from python, it is possible to call a function using python like syntax (`get_summary()`) which does not specify the function type. In order to set the function type here, you need to use a function decorator (`@function`,`@global_function`, `@local_function`) above where the function is defined in the code. Functions without decorators are assumed to be of type "local_function" since this is the most similar to native python functions. It's not currently possible to set the function type of the called node using `exec_node`, so function calls to functions defined this way should also be made using the `exec_node` method, where the function type can be defined by the action of the calling node. 


It is also possible to pass arguments to AutoGRAMS functions. Arguments can be variables or python literals. 


Option 3.

```
# add earlier chat nodes here
# ...
variable1="here is some additional context"
variable2="here is some more additional context"

summary = get_summary(variable1,variable2)

# add later chat nodes here
# ...

@function
def get_summary(variable1,variable2):
  summary = exec_node(action="thought",instruction="Here is some past context $variable1\n$variable2\nWrite a summary of the conversation so far.")
  return summary
```

It is not currently possible to implement nested AutoGRAMS function calls in a single statement, so code like `summary = get_summary(get_variable(),variable2)` will not run correctly, although assuming you had another method called `get_variable()`, you could implement this as 2 separate statements as

```
variable1=get_variable()
summary= get_summary(variable1,variable2)
```

It is also possible to call functions with arguments directly with nodes. option 3 is compiled to be equivalent to the following

Option 3b

```
# add earlier chat nodes here
# ...

exec_node(action="python_function ",instruction="variable1='here is some context'")
exec_node(action="python_function ",instruction="variable2='here is some additional context'")

exec_node(action="function",instruction="summary=get_summary(variable1,variable2)")

# add later chat nodes here
# ...

exec_node(name="get_summary(variable1,variable2)",action="thought",instruction="instruction="Here is some past context $variable1\n$variable2\nWrite a summary of the conversation so far.",transitions=["return"])

```


### function

The "function" action in AutoGRAMS calls a callable node as a function. Its scope allows it to see the past conversation history and autogram, but new variables or conversation turns are not remembered once the function returns, other than the variables that are returned. When coding in AutoGRAMS compiled from python, functions can be called and defined with normal python syntax, and the function type is determined by a function decorator (which should be either @function, @global_function, or @local_function). 



```
new_problem=make_problem()

@function
def make_problem():
    problem= exec_node(
        action = 'thought',
        instruction = 'Write a new problem for the user to solve that tests their understanding of the material.'
        )
    return problem
```
Note that multiple returns are not allowed, but can be effectively accomplished by making a list or dictionary and returning that.

To define a function action directly in a node, set the action to function and include the function call in the instruction.
```
exec_node(
  action="function",
  instruction="new_problem=make_problem()"
)
```

### local_function

The `local_function` action works similarly to `function`, but as the name suggests it is a purely local function. It can only see arguments that are passed to it, and it can only pass results back to the calling scope in its return. 

```
answer=check_answer(problem)

@local_function
def check_answer(problem):
    answer = exec_node(
        action = 'thought',
        instruction = 'consider the problem $problem . Reply with the answer to the problem and nothing else.'
        )
    return answer
```

### global_function
The `local_function` action works similarly to `function`, but it can see the entire state of the autogram, and new conversation turns or variables defined in a global function will stay in memory after the function returns