# Node subtypes

Nodes in AutoGRAMS are objects with an inheritance structure reflected by the action of the node. Node classes are implemented in the /autograms/nodes folder. All nodes inherit from the (abstract) BaseNode class, and override certain methods from that class to implement custom behaviors. This section explains how nodes work in greater depth, and also explains how to implement custom nodes. 



Technically, any method in BaseNode could be overriden by a node subtype, but here we describe the main ones that we override to create custom behavior and distinguish node subtypes from each other.

Here is the structure of the node classes. 

```
BaseNode (abstract)
├── ThoughtNode
│   ├── ThoughtQANode
│   └── ThoughtExactNode
├── ChatNode
│   ├── ChatSuffixNode
│   └── ChatExactNode
├── FunctionNode
    ├── GlobalFunctionNode
    └── LocalFunctionNode
├── PromptModifierNode (abstract)
    ├── SetPromptNode
    ├── SetUserPromptNode
    ├── AppendPromptNode
    └── AppendUserPromptNode
├── PythonNode
└── TransitionNode

```


Every node that is not abstract corresponds to an action, defined by the keys in the dictionary `NODETYPES` in `/autograms/nodes/__init__.py`

## `__init__` function in node subtypes

The init function for a node subtype should use arguments in the following order:

1. autogram_config - used for autogram settings
2. statement_interpreter -- used to interpret python statements
3. node type specific args (if any)
4. **kwargs -- the node fields

The `__init__` function must call super() to initialize the parent class. Here is an example for the node for the "function" action, which inherits from BaseNode directly

```
def __init__(self,autogram_config,statement_interpreter=None,function_type="normal",**kwargs):
    super().__init__(autogram_config,statement_interpreter,**kwargs)

    self.function_type = function_type
```


## apply_instruction()

Apply instruction determines the main behavior of the node, and is the most common to override. It takes the following arguments:

1. user_reply - the most recent reply from the user, or the empty string if the reply was consumed by another node
2. memory_object - an object that maintains the state of the program, including variables and conversation turns
3. chatbot -- the model that generates chat replies and thought replies
4. nodes -- an OrderedDict type containing all the nodes in the program

The steps involved in the apply_instruction method can vary by node type. Some nodes will need to replace variables in the instruction, form the prompt, call the chatbot, and get the result. Others simply just need to update the memory object to log the state. At the minimum an instruction node should contain `memory_object.append_state(self.name)`. It also must give 3 returns

1. response -- the output of the node, can be set to None for a node with no output
2. new_user_reply -- the new user reply, right now this is either the empty string (which overwrites old user reply) or None- which maintains old user_reply. Generally this should be the empty string if the model uses the user reply in the prompt, otherwise None.
3. response_to_user -- a boolean that determines if we should return the response to the user. True for chat nodes and chat subtypes, false otherwise

Here is an example of the apply instruction for the ChatNode for the chat action

```
def apply_instruction(self,user_reply,memory_object,chatbot,nodes):

    instruction = set_variables(self.instruction,memory_object.get_variable_dict())


    """
    ChatNodes retain instruction in the prompt when either:
        - the previous user reply wasn't defined (for instance if a thought node was called before replying)
        - the instruction contains variables -- these could be useful to be viewed at future turns

    Otherwise, the instruction applied here becomes invisible to the model during later turns of the conversation to prevent prompt from getting too crowded
    """
    if len(user_reply)==0:
        retain_instruction=True
    else:
        retain_instruction = check_contains_variables(self.instruction,memory_object)


    required_text=""

    start_prompt=memory_object.get_prompt()
    turns = memory_object.get_thought_chat_turns()
    input_turns =turns + [{"user_reply":user_reply, "instruction":instruction}]

    inputs,outputs,prefix = self.make_prompt(input_turns,start_prompt,required_category=self.conv_scope,transition=False,nodes=nodes)


    response,success=apply_chatbot(chatbot,memory_object,inputs,outputs,prefix,required_text,self.name)


    memory_object.append_state(self.name)
    turn_dict = {"retain_instruction":retain_instruction,"user_reply":user_reply,"agent_reply":response,"instruction":instruction,"state":self.name,"category":self.state_category,"is_reply":True}
    memory_object.append_turn(**turn_dict)


    response_to_user=True

    #set for any node that consumes input
    new_user_reply=""

    return response,new_user_reply,response_to_user
```

## apply_transition()

apply_transition() determines what state the autogram will go to next after visiting a node. Node subtypes can have specific apply_transition() functions. 


apply_transition() Takes 4 arguments:


1. user_reply - the most recent reply from the user, or the empty string if the reply was consumed by another node
2. memory_object - an object that maintains the state of the program, including variables and conversation turns
3. classifier -- A language model that predicts the answer to multiple choice questions
4. nodes -- an OrderedDict type containing all the nodes in the program
5. autogram_config -- the autogram's settings



The only return argument will be the `new_node_id`, a string that gives the name of the next node the autogram should transition to. `new_node_id` is the unprocessed node name, so it could contain `.*` or `.n` syntax, in which case the exact name of the next node will be determined at a later post processing step.

Many node types can inherit their apply_transition() function from a specific node. For instance all ThoughtNode objects and subtypes just inherit directly from BaseNode's transition function. This transition function sets any variables referenced by `$` in the `transition_question`, forms the transition prompt, and applies the classifier to get the prediction. The apply_transition function for BaseNode is given below:

```
def apply_transition(self,user_reply,memory_object,classifier,nodes,autogram_config):
    """
    Decides which transition to predict for the next state. 
    Behavior is sometimes different for different node types. For instance function nodes need to be able to transition to the node being called in the function.

    args:
        user_reply -- user's previous reply
        memory_object -- MemoryObject defining conversation history
        classifier -- model used to predict multiple choice answer
        nodes -- all nodes in autogram
        autogram_config -- AutogramConfig object with default autogram settings

    returns:
        new_node_id -- predicted transitions
    
    """
    if self.transition_question is None:
        transition_question=self.transition_question
    else:

        transition_question = set_variables(self.transition_question,memory_object.get_variable_dict())

    start_prompt=""
    turns = memory_object.get_turns()
    
    input_turns =turns + [{"user_reply":user_reply, "instruction":""}]

    inputs,outputs,_ = self.make_prompt(input_turns,start_prompt,required_category=None,max_turns=self.transition_context,transition=True,nodes=nodes)

    #predicts next state, only actually calls classifier if there are is than 1 possible transition
    node_pred = self.predict_next_state(inputs,outputs,classifier,transition_question,memory_object)

    new_node_id=node_pred

    return new_node_id
```


Some node types have different apply_transition functions. ChatNode objects and their subtypes have an extra step to predict interjections-- if the autogram has interjection nodes that can be reached after any ChatNode, we need to predict whether we should jump to any of these nodes. 

FunctionNode objects and their subtypes are responsible for calling functions, and therefore need very different transition behavior. When an autograms function is called, a function node will be reached twice--once during the call, and again when the function returns. During the call, the functions apply_transition() function returns the name of the node that the function is calling. During the return, the transition behavior of a function node is similar to that of a base node.

## get_variable_output()

Nodes may output a variable when they execute. This result is returned to a special variable called "last_variable_output", as well as any variables that are assigned at that node (ex: `var1=exec_node(...)`). Different node types may want to return something different as the variable output. The default behavior of the BaseNode is given below:


```
def get_variable_output(self,user_reply,memory_obj):
    """
    Decides what the output to the variables that are assigned this turn should be. 
    This behavior may be different for different node types. 
    Most commonly will be the model's reply, but may also combine the instruction or the last user reply. 
    For function call nodes, it will be whatever was returned by that function
    For some other nodes, no variables are assigned and this will be the empty string

    args:
        user_reply -- user's previous reply
        memory_obj -- MemoryObject defining conversation history

    returns:
        variable_output -- variable set by this node

    
    """

    last_reply =memory_obj.get_last_reply()

    if last_reply is not None:
        variable_output=last_reply
    else:
        variable_output=None

    
    return variable_output

```





## implementing custom node types

If you need a node that has different behaviors in one or more of these methods, you can implement a custom node. The easiest way to do this is to define a new node in the nodes(`/autograms/nodes/`) folder. Be sure your node calls inherits from either BaseNode or another node subtype, and the `__init__` method calls super() appropriately. Then you can override whichever methods you would like to change. Be sure to use the same arguments as the original method, even if they are not all actually used in your function.

Once you have implemented your nodes, open into the `/autograms/nodes/__init__.py` file. You need to import your new node class in this file (see the other examples in the file). You will also need to add your node to the NODE_TYPES dictionary, which maps action names to node classes. Set the key to what you want the action to be called, and the value to the class you've created. autograms will use this dictionary to recognize the action you've created so that you can define nodes with this action.

When you are done, move to the root directory and use `pip install .` to reinstall.

