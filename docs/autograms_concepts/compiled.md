# AutoGRAMS compiled from python

AutoGRAMS compiled from python is technically a new programming language that very closely overlaps with python and relies on the python interpreter heavily. It is also possible to code any AutoGRAMS program in pure python (or a spreadsheet) by defining nodes one by one, and would likely make sense for agents consisting mainly of a network chat nodes. However for autograms that contain python statements or programmatic features like loops and conditionals, the compiled version has several advantages:

- Allows for python statements to be included directly as code instead of as strings in the instruction of python_function nodes

- Allows for python style variable assignments to be used instead of assignment variable in an instruction

- Allows for AutoGRAMS function calls and functions to be defined using python-like syntax

- Allows the order of node chains to be inferred automatically from the order they appear in code, even if names and transitions aren't defined.


- Allows for python loops and if/else conditionals to compile into a graph automatically.

    - AutoGRAMS conditionals can be facilitated by .* transitions and corresponding .a and .b nodes with the `boolean_condition` attribute set appropriately. In AutoGRAMS compiled from python, you can implement this as an if/else statement and the appropriate nodes will be compiled automatically from the code.

    - AutoGRAMS loops are implemented as a chain of nodes that loops back onto itself, with a conditional to break out of the loop. In AutoGRAMS compiled from python, you can implement this using normal `for` or `while` loop syntax, and the graph will automatically compile into the loop described in the code.


Being able to code with python-like syntax also allows you to use your favorite editor to check for warnings and bugs in the autogram. When coding in pure python, these warnings and bugs would appear in strings defined as fields of the nodes, so they wouldn't be noticeable by the editor.


## The ExecNode() method and other AutoGRAMS built ins

The `ExecNode()` method is used to define nodes in AutoGRAMS compiled from python. It is built in, so it does not need to be imported. ExecNode() defines a node and will execute that node at the point in the code where the ExecNode() statement is used. To see a complete list of arguments ExecNode accepts, see the [glossary of node_fields](node_fields.md). The arguments are the same as the agent.add_node() method if using pure python.


### DebugCheckpoint()

When using AutoGRAMS compiled from python (or any autogram), the `DebugCheckpoint()` function can be used to create a node that pauses the program and loads the state of the variables. It creates a pdb checkpoint that creates an interactive terminal that the programmer can interact with at that point in the program. It is also possible to use `pdb` checkpoints directly in AutoGRAMS code if `pdb` is included in the `python_modules` or `python_imports` of the [AutogramConfig](autogram_configs.md), however the scope of this checkpoint will only allow python variables visible from that point in the code to be seen. The `DebugCheckpoint()` method allows access to the memory object, which contains all variables as well as the entire state of the program.





## variable assignments and use

Variable Assignments work similarly to normal python variable assignments. The following 3 statements are all equivalent in AutoGRAMS compiled from python.


1. `ExecNode("action="python_function",instruction="str1='hello'")`

2. `str1=ExecNode("action="python_function",instruction="'hello'")`

3. `str1='hello'`

The internal AutoGRAMS representation looks most like statement 1, but the AutoGRAMS compiler is able to read and convert statement 3 into the node described by statement 1.


### Direct references vs $ syntax


Direct variable references can be used in python_function nodes (or python statements that compile to python function nodes). This method of referencing directly references the variable in python code. This method of variable use is distinctly different from referencing a variable using the $ syntax, which embeds the variable as a string directly into an instruction string, and is mainly meant for non-python function nodes. 

When using variables in python statements or python_function instructions, it is possible to reference that variable directly. For instance it is valid to have both of the following statements the reference str1.


1. `ExecNode("action="python_function",instruction="str2=str1+'goodbye'")`

2. `str2=str1+'goodbye'`

If you would like the actual string of the instruction to vary at run time, you would need to use the `$` variable syntax. 

So for instance,

`ExecNode(action="chat",instruction= "say $str1 to the user")`

Would give an instruction to say hello to the user. 


The following looks misleadingly equivalent but is not valid:

`ExecNode(action="chat",instruction= "say " + str1 + " to the user")`

And the reason is because the instruction string must be formed at compile time, and `str1` is not defined at compile time--it is defined during the actual execution of the program.


The following is valid but inadvisable for many applications:


`ExecNode(action="python_function",instruction= "str2='$str1' + 'goodbye')`

Using $ syntax in a `python_function` instruction is effectively is doing code injection, which can be insecure for many applications. When the above instruction is reached, str1 will be embedded into the instruction, resulting in an instruction of  "str2='hello' + 'goodbye'". Note that we needed to also wrap single quotes around `$str1` or else it will become `"str2=hello + 'goodbye'"` which will give an error because `hello` is not defined. It is not possible to use $ variable embedding for python code written outside of a node instruction.






## Inferring node order and "next" transition

The order of nodes in AutoGRAMS compiled from python is automatically inferred from the order they appear in the code if no transitions are defined. For instance the following block: 


```
ExecNode(action="chat",instruction= "Ask the user about their background.")
ExecNode(action="chat",instruction= "Respond to the user and probe the user to give more details about their background.")
ExecNode(action="chat",instruction= "Respond to the user and ask the user about a challenge they faced and overcame.")
```
These nodes will execute these nodes sequentially in a chain, giving them automatic names and linear transitions.

There is also a special type of transition called "next" that is only valid in AutoGRAMS compiled from python. "next" can be used when there is more than 1 possible transitions, one of which is the next node in the code.

```
ExecNode(action="chat",
    instruction= "Ask the user about their background.",
    transitions=["next","ask_challenge"]
    transition_question="did the user describe their background in detail (more than two sentences)?"
    transition_choices=["no","yes"])

ExecNode(action="chat",instruction= "Respond to the user and ask the user a follow up question about their background.")
ExecNode(name="ask_challenge",action="chat",instruction= "Respond to the user and ask the user about a challenge they faced and overcame.")
```
The above block will execute sequentially due to the "next" transition if the user does not detailed answer about their background, and will skip the middle node otherwise.




## functions and function calls

AutoGRAMS functions can be defined using similar syntax to python functions. You can put define functions anywhere it the program, the compiler reads the functions first and then reads code outside of a function.





## loops and conditionals


Loops and conditionals can be defined in the same way as python, using `while` or `for` for loops, and `if`/`elif`/`else` for conditionals. Conditionals will use .* transitions with automatically named nodes to facilitate the branch logic, and loops will result in a graph that loops back on itself with automatically generated nodes to handle the exit conditions of the loop.






## Controlling imports



No imports are used in AutoGRAMS compiled with python, instead these are set as part of the [AutogramConfig](autogram_configs.md) using the  `python_modules` or `python_imports` fields . It is necessary for the modules set in the autogram config to match the python modules used in the code.


## Compiling a normal python program into an AutoGRAMS graph


- Most python programs that consistent only of functions can be compiled into an AutoGRAMS graph. 
- Any python not supported can be treated as an external python function call from AutoGRAMS
    - python classes used in the program must be defined externally, see [unsupported behaviors](#unsupported-behaviors)




## unsupported behaviors

- multiple variable assignments in a single statement is not supported in AutoGRAMS and is also not supported in AutoGRAMS compiled in python. So a statement like `x,y=0,0` will give an error. We are likely to support this in the future for AutoGRAMS compiled from python, since the compiler could automatically divide this into multiple statements.

- class definitions
    AutoGRAMS does not allow class definitions internally within the language. However, it is still able to use python objects that are returned by python functions. If you want to define classes to use in your program, it is best to define them externally, load them using the `python_modules` attribute when you initialize agent config. You will then be able to initialize and use these classes from within AutoGRAMS.

- transitioning into a loop

    Transitioning from outside of a loop to inside of a loop is not supported. Consider the following example 

    ```
    exec_node(action="transition",transitions=["loop_node"])

    for i in range(5):
        exec_node(action="transition", name="loop_node")
        print(i)

    ```
    
    When the first node transitions to "loop_node", it will skip the steps needed to initialize the loop, so there will be errors when the agent reaches the start of the next iteration of the loop since the iterator won't be defined. While transitioning into a loop is not supported, transitioning out of a loop should work correctly.






