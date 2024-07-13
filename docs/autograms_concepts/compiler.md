# AutoGRAMS compiler


The AutoGRAMS compiler reads in AutoGRAMS compiled from python, and compiles an AutoGRAMS graph. It is not a traditional compiler in the sense that it does not create machine code. What it does do is translate code with python-like syntax into a representation that the AutoGRAMS interpreter can understand. The autogram compiler is implemented in `autograms/autogram_compiler.py`






## high level steps

AutoGRAMS compiler processes code down to the level of individual nodes and statements, and to form an AutoGRAMS graph around these statements. It relies on the python abstract syntax tree (AST) to parse the code, and recursively traverses the AST until it reaches code that can be represented as a single statement or AutoGRAMS node.

The `__call__` function of the autogram compiler takes in a code string and an initial AutogramConfig, and returns an autogram, for instance like in the following code:

```
from autograms import AutogramConfig, AutogramCompiler
config = AutogramConfig()
with open("some_code.py") as f:
    code=f.read()

compiler = AutogramCompiler()

autogram = compiler(code,config)

```

The `__call__` function of the autogram compiler (which is reached by calling `compiler(code,config)` in the above code) has several steps.

1. Convert code to python AST representation
2. Extract the name of every function definition in the code and the subtree of the AST associated with that function
3. Recursively traverse the subtree of the AST for each function to get the AutoGRAMS graph for that function
4. Recursively traverse the AST for code that is outside of a function to get the AutoGRAMS graph of the outer scope/main program

The autograms compiler assumes their are no nested function definitions (these are not supported in autograms--although you can of course call functions inside of functions). 




## Compiling the graph from the AST

The main step of the AutoGRAMS compiler is to convert ASTs into AutoGRAMS graphs, which then can be used to create an autogram. This uses the `compile_from_ast` method to recursively traverse the AST. The AST is a tree representation of the program that uses nesting to structure the program. So for instance in a loop, every statement in the loop will be descended from a node in the AST representing that loop. The AST can model nested loops too by having a loop node with its own subtree that are descended from the parent outer loop node. The AST is structured in a similar way for conditionals and functions. In recursive AST traversal, the `compile_from_ast` method starts at the root node of an AST (or a subtree of an AST) and recursively calls `compile_from_ast` on the children of that root node. For each child AST node, depending on the AST node type (distinct from AutoGRAMS node type), `compile_from_ast` has different behavior. Once it gets to child AST nodes on the level of single statements, it adds an AutoGRAMS node that corresponds to the statement. 


The `compile_from_ast` method takes 2 arguments, the AST node, and an object of type `AutogramCompilerChain`. An `AutogramCompilerChain` stores the appropriate arguments for a series of AutoGRAMS nodes. Every time a single statement is encountered in the AST, it is used to add the arguments for an AutoGRAMS node to the current `AutogramCompilerChain`. When the `compile_from_ast` encounters an AST node corresponding to a loop or conditional, it creates a new child `AutogramCompilerChain`. The body of the loop/conditional is processed recursively and added to this child `AutogramCompilerChain`. Once this is done, the child `AutogramCompilerChain` is merged wth the parent `AutogramCompilerChain`, with additional nodes added to handle the conditional or loop logic around the child chain. 



### Compiling conditionals

When encountering an AST node corresponding to a conditional, the compiler collects the following for each branch:

1. the conditional statement for that branch
2. A new AutogramCompilerChain for that branch (by recursive traversal)

After collecting these, the compiler calls the AutogramCompilerChain.add_conditional() method to add the conditional to the parent compiler chain. It works by using `.*` style transition to model each of the conditions. This creates a `.a`, `.b`, etc. AutoGRAMS node at the start of each conditional branch. The `.*` transition is set before the branch, and then the `.a`, `.b` etc nodes have their `boolean_condition` attribute set to the condition for the branch. The AutoGRAMS nodes in the subchain for each branch are then appended after the corresponding start node for that branch.

After the all the boolean conditions have been added to the parent AutogramCompilerChain, the AutogramCompilerChain is returned, where it could either be processed as the full program or as the child of another AutogramCompilerChain.


### Compiling while loops

When encountering an AST node corresponding to a while loop, the compiler collects:

1. the condition for the while loop
2. A new AutogramCompilerChain for that body of the while loop (by recursive traversal)


After collecting these, the compiler calls the AutogramCompilerChain.add_while_loop(). An entrance node with a `.*` style transition is created at the start of the while loop to facilitate a conditional. Then a `.a` node is created with a boolean_condition attribute matching the boolean condition of the while loop--meaning that this node will be reached when the while loop condition is true. A `.b` node is included to exit the while loop when the condition is not met. The `.a` node transitions to the first node in the while loops child AutogramCompilerChain created from the while loop body. The last node in the compiler chain is connected to a `.*` style transition that goes back to the loop decision nodes, either continuing the loop with the `.a` node if the boolean condition is met, or exiting it if it is not.


After the while loop has been fully incorporated into the parent AutogramCompilerChain, the AutogramCompilerChain is returned.
### Compiling for loops

When encountering an AST node corresponding to a for loop, the compiler collects:

1. the name of the iterator element
2. the iterable to be used
3. A new AutogramCompilerChain for that body of the for loop (by recursive traversal)


After collecting these, the compiler calls the AutogramCompilerChain.add_for_loop(). The for loop is implemented as a while loop, with an additional iterator and counter variable that are added. A special variable called `_forloop_iterable` is used to store whatever is set as the for loop iterable, and a special `_forloop_counter` is used to store how many iterations the loop has gone through. If the for loop is written for instance as:

`for i in range(3,6):`
Then the `_forloop_iterable` is set to `range(3,6)`, and at each iteration, a variable `i` is set to the `_forloop_counter`th element of `range(3,6)`. All of these operations are facilitated using `python_function` nodes. The loops conditional checks to see if `_forloop_counter` is still less than the length of `_forloop_iterable`, and like with the while loop, using a `.*` style transition with `.a` and `.b` nodes to accomplish this. 







<!-- ### compiling assignments


### compiling statements


### compiling returns -->





