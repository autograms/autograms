# Overview of AutoGRAMS concepts

* [AutoGRAMS basics](autograms_basics.md) -- gives an introduction to the main features and necessary concepts needed to understand and use AutoGRAMS. It includes:

    - [Initializing the autogram](autograms_basics.md/#initializing-the-autogram) -- shows how to load or define an autogram in python
    - [Getting replies](autograms_basics.md/#getting-replies) -- shows how to get a reply from an initialized autogram chatbot
    - [Nodes](autograms_basics.md/#nodes) -- all autograms are composed of a set of nodes which the autogram's designer must specify. 
    - [Transitions](autograms_basics.md/#transitions) --  Each node applies a transition to select another node after executing. Several fields define how the node selects which node will come next
    - [Instructions](autograms_basics.md/#instructions) -- Each node has an `instruction` field that in combination with the `action` field define what happens when the node executes. Depending on the action, the instruction may for instance be interpreted as a language model prompt or Python code to execute.
    - [Internal functions and scopes](autograms_basics.md/#internal-functions-and-scopes) -- describes how to execute AutoGRAMS graphs as callable modules
    - [Calling AutoGRAMS functions from python](autograms_basics.md/#calling-autograms-functions-from-python) -- describes how AutoGRAMS graphs designed as callable modules can be called directly from Python.
    - [Python functions](autograms_basics.md/#python-functions) -- describes how Python code can be embedded within an AutoGRAMS node
    - [Variables](autograms_basics.md/#variables) -- describes how nodes can be used to set variables in memory, and how to reference these variables to use them later.
    - [Memory Object](autograms_basics.md/#memory-object) -- introduces how memory is managed in AutoGRAMS

* [Nodes and actions](actions.md) -- `action` is a node field that define how the node's instruction will be interpreted, and determines what type of node it is. This page describes all the actions available in AutoGRAMS.

* [Transitions](transitions.md) -- Detailed guide transitions in AutoGRAMS that describes them in more depth and gives more examples

* [Interjection Nodes](interjection.md) -- Guide to a special type of node called an "interjection node "that allows transitions from any other chat node.

* [Autogram Config](autogram_configs.md) -- describes Autogram config, a python class used to define general agent settings such as what language models to use or what prompt template to use.

* [Prompt formation](prompts.md) -- describes how prompts are formed in AutoGRAMS, using a combination of the language model turn history and the node specific instructions
* [Models and generation](models.md) - describes how models are used to generate text for replies and classify multiple choice questions for transitions

* [AutoGRAMS Compiled from Python](compiled.md) -- describes how to code autograms using python like syntax. This method of implementation is convenient for integrating Python code more deeply with AutoGRAMS nodes.



* [Node Subtypes](node_subtypes.md) -- A detailed overview of the class structure and behavior of node subtypes, which are determined by a node's [action](actions.md) when it is defined.

* [Understanding the interpreter](interpreter.md) -- Explains how autograms are executed under the hood

* [Autogram Compiler](interpreter.md) -- Explains how python-like code in [AutoGRAMS compiled from Python](compiled.md) is converted to an set of AutoGRAMS nodes using the Python abstract syntax tree

* [Glossary of node fields](node_fields.md) -- Describes all the different fields that can be set for AutoGRAMS nodes 








