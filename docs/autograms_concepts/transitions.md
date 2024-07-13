# Transitions

There are several ways to have transitions in the AutoGRAMS. For transitions predicted by the agent's classifier, you need to initialize a node with a list of transitions, a transition question, and a list of transition answers with a one to one correspondence to the transitions.



## Basic transitions


```
exec_node(name="ask_math_problem",
    transitions=["answer_correct","answer_incorrect","asked_question","user_not_sure"],
    action="chat",
    "instruction"="Make up an simple algebra problem fo the user to solve, and include this in your reply.",
    transition_question="What did the user do?",
    transition_choices=["gave a correct answer","gave an incorrect answer","asked a question","wasn't sure where to start"])
```

In this case, there are 4 possible transitions, and 4 corresponding transition choices. The classifier chooses which transition choice most applies based on the user response, and this decides the transition. Note that you do need need a `transition_question` or `transition_choices` if there is only 1 possible transition.

## Simulating transitions from the user's side

In order to simulate conversations, you can add a list attribute called `user_instruction_transitions` to a node to instruct the userbot on what to do in each transition scenario. You still need to define `user_instruction_transitions` if the number of transitions is 1 if you would like to be able to simulate the user--in this case the length of the `user_instruction_transitions` list would also be 1. Here is an example with 1 user instruction for each transition. The `user_instruction_transitions`, `transition_choices`, and `transitions` all align with each other.

```
exec_node(name="ask_math_problem",
    transitions=["answer_correct","answer_incorrect","asked_question","user_not_sure"],
    action="chat",
    "instruction"="Make up an simple algebra problem fo the user to solve, and include this in your reply.",
    transition_question="What did the user do?",
    transition_choices=["gave a correct answer","gave an incorrect answer","asked a question",
    "wasn't sure where to start"]
    user_instruction_transitions = ['give a correct answer', 'give an incorrect answer','ask a question','say you are not sure'])
```



## Nested transitions

Some times it may make sense to break up a transition into more than 1 multiple choice question. For instance, the above example may be executed as follows: 


```
exec_node(name="ask_math_problem",
    transitions=["gives_answer","does_not_give_answer"],
    action="chat",
    "instruction"="Make up an simple algebra problem fo the user to solve, and include this in your reply.",
    transition_question="did the suer give an answer?",
    transition_choices=["yes","no]
    user_instruction_transitions = ['answer the question correctly or incorrectly','say you are not sure or ask a question'])


exec_node(name="gives_answer",
    transitions=["answer_correct","answer_incorrect"],
    action="transition",
    transition_question="is the user's answer correct?",
    transition_choices=["yes","no])

```

"transition" nodes make useful placeholders and also allow for additional branch points.
Note that only chat nodes can make use of user instructions, so a autogram like the above may not as reliably simulate every possible user scenario.




## .* transitions



Transition names with special syntax also allow for more complex behavior. There are 2 special syntaxes that transitions can use, For instance `transitions = [state1.*]` Can transition to states `state1.A`, or `state1.B`, or `state1.C` etc. if more lettered states are defined. The `.*` syntax can be used to effectively implement if else statements, depending on the fields set for `state1.A` and `state1.B`. 




## .n transitions

Another special syntax `transitions = [state1.n]` will go to `state1.1` n the first visit, `state1.2` on the second visit, etc.




## interjection transitions

When using interjection nodes, it is possible to transition from any chat node to any interjection node. This is done using a separate multiple choice question that is asked before the main transition



## dynamic transitions

It is possible to use dynamic transitions by using $ syntax in transitions. This feature is still experimental though, and can cause a autogram to crash if the transition isn't defined carefully. For instance, the following example

```
node_name="check_answer"
exec_node(action="transition",
    transitions=["$node_name])
```

Should transition to the node identified by the variable `node_name`, which can be set during the autogram.

## overview of all transitions

All full process for selecting a transition is shown in the diagram below

<iframe src="../images/autograms_apply_transtion.png" max-width="100%" height="500px" width="100%"></iframe>





