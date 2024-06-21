# Interjection Nodes


"Interjection nodes" are nodes that can be reached after any chat node. They are mostly meant for scenarios where the user does or says something unexpected and it may be neccessary to leave the main conversational trajectory. They can be any action type. The way to make a node an interjection node is to define a `condition_interjection` field when making a node. 


```
exec_node(name="change_topic",
 action="chat", 
 condition_interjection="The user wants to change the topic.",
 instruction="Confirm with the user about what they would like to talk about.")
```


The default interjection question is `"Which of the following is True?"`. The last answer, by default, is `"None of the above."`. These defaults can be changed in the AutogramConfig. 

So in the above case, if the "change_topic" node is the only node with "condition_interjection" defined, immediately after getting a new user reply,  the classifier will see a multiple choice question like:

```
Which of the following is True?

A. The user wants to change the topic
B. None of the Above
```

If the classifier predicts that the answer is A, then the autogram will jump to the `change_topic` node, where it will confirm with the user what they would like to talk about. If the classifier predicts B, the autogram will continue along the graph as normal. Interjection transitions are predicted before normal transitions, so the normal transition won't be executed if an interjection transiiton is predicted. If the autogram has no interjection node, the step to predict interjections will be skipped.s






It is important to define the answers for interjection transitions carefully, since if the model incorrectly predicts and interjection transition it can lead to large breaks in the conversational flow. It should be possible to have up to 25 interjection nodes defined in an autogram, however doing so might increase the probability that the model incorrectly breaks the conversation, since the classifier would need to choices "None of the above" out of 26 choices whenever the conversation needs to continue as normal. Another option to having many interjection choices would be to have 1 or 2 interjection nodes, and to have additional branching after the interjection.

For instance, consider the following interjection node:


```
exec_node(name="change_topic",
 action="transition", 
 condition_interjection="The user wants to change the topic.",
 transitions=["talk_politics","talk_sports","talk_movies","talk_other"],
 transition_question="Which of the following does the user want to talk about?,
 transition_choices["politics","sports","movies","something else"])
```

While it would be possible to have a separate interjection node for every possible topic change a user might want, it is better in most situations to first predict that the user wants to change the topic, and then predict what they want to change the topic to by making the interjection node a transition node. This will likely reduce the probability that the classifier predicts an erroneous topic change interjection.




## Other fields for interjection Nodes


The `condition_interjection` field described above is what makes a node an interjection node--if this is defined a node will be treated as an interjection node.


The  `example_interjection` field allows you to give additional context the model to help it correctly predict an interjection. For instance in the example above example, you might set this field to 
```
"""Here are some examples of users that want to change the topic
User: I'm bored of this
User: can we talk about what I should watch tonight.
User: let's talk about something else
"""
```

Providing examples can greatly improve the classifier's accuracy in predicting interjections, which is pretty important for correctly controlling the flow of the conversation.

The `probability_interjection` and `user_interjection` are used for simulating interjections when simulating user interactions with the autogram. In the above example, we might set the `user_interjection` to `"say that you want to change the topic"`, which will instruct the userbot to simulate a user that wants to change the topic. The probability interjection is a float between 0 and 1 that determines what frequency to sample this interjection during simulation.



