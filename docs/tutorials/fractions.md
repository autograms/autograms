
# Fraction tutor chatbot

Here we are going to use AutoGRAMS to code a fraction tutor chatbot. To follow along with this, make a new directory called `tutorial_examples/fractions/`, and create a new file in that directory called called fraction_tutorial.py . This tutorial will use AutoGRAMS compiled from python to make this chatbot step by step.


For our fraction tutor, we want it to go through several units with the user. For each unit, we want it to describe the material it's teaching, and give the user practice problems. We need the user to be able to ask questions and decide the pace that they would like to move through the lessons.



## adding initial prompts
To start, let's add nodes that give the initial prompts for the autogram and for the user simulator. The `'set_prompt'` and `'set_user_prompt'` actions will accomplish this. Remember, we don't need any imports in this file because imports are handled at the autogram's initialization.

```
exec_node(
      action = 'set_prompt',
      name = 'start1',
      instruction = ('You are tutor for the subject of fractions. Your goal is to teach the student what fractions are,' 
      'as well as how to reduce, add, multiply and divide fractions.' 
      'Follow all instructions and be sure to make sure the user understands before continuing with each step.'),
      )

exec_node(
      action = 'set_user_prompt',
      name = 'start2',
      instruction = 'You are a student (the user) trying to learn the subject of fractions from a teacher.',
      )
```


## coding the introduction
Now let's code the first chat node where the tutor introduces itself. We give an instruction to the autogram for how to introduce itself, as well as an instruction to the userbot to simulate how the user could reply. 

```
exec_node(
      action = 'chat',
      name = 'intro',
      instruction = ('Introduce yourself as a tutor named fractobot.'
      'Ask the user how they are and how much they have previously learned about the subject'),
      user_instruction_transitions = ["tell the tutor you don't know much about it but are excited to learn"],
      )
```

After the introduction, we want the bot to ask the user if they are ready to begin. the user may be ready or may ask a question first, so we create 2 transitions to simulate these possibilities.
```

exec_node(
      action = 'chat',
      name = 'intro2',
      transitions = ['intro3', 'intro2b'],
      instruction = 'respond to the user and ask if they are ready to begin',
      transition_question = 'Does the user have any questions yet?',
      transition_choices = ['no', 'yes'],
      user_instruction_transitions = ['say you are ready',\
      'say that before you begin you have a question, and ask the question'],
      )
```
Next, let's add the node to handle when the user isn't ready. As long as the user has more questions, we keep revisiting this node to answer them, otherwise we proceed to the next step in the conversation
```
exec_node(
      action = 'chat',
      name = 'intro2b',
      transitions = ['intro2b', 'intro3'],
      instruction = 'respond to user',
      transition_question = 'Does the user have any more questions?',
      transition_choices = ['no', 'yes'],
      user_instruction_transitions = ['say you are ready now', 'ask another question'],
      )
```

Let's save our file and visualize what we have so far. It can useful to be periodically draw the graph of the autogram as we code. Go back to the root directory of AutoGRAMS and run 

`python make_interactive_graph.py --autogram_file tutorial_examples/fractions/fraction_tutorial.py`

This should save 3 files, including a file called `tutorial_examples/fractions/fraction_tutorial_full_graph.html`. The graph should look like this:

<iframe src="../../agent_graphs/fraction_tutor/example1.html" width="100%" height="500px"></iframe>
Click on any node to see details. However over the graph and scroll to zoom in or out.

There is an undefined note in the graph for "intro3" since we referenced that in transitions but haven't defined that yet. so let's make "intro3". We will start to dive into the material in intro3 by describing what a fraction is at a high level. We will have 2 transitions, one that moves onto the first unit, and one that addresses any questions the user has

```
exec_node(
      action = 'chat',
      name = 'intro3',
      transitions = ['start_units', 'intro3b'],
      instruction = ('describe what a fraction is at a high level,'
      'adding on to anything the user has previously said. Ask the user if they have any questions'),
      transition_question = 'Does the user have any questions?',
      transition_choices = ['no', 'yes'],
      user_instruction_transitions = ['say that sounds good so far', 'ask a question'],
      )
```

Like previous node to address questions, we have one transition to stay at the same node and answer more questions, and another transition to move on.
```
exec_node(
      action = 'chat',
      name = 'intro3b',
      transitions = ['start_units', 'intro3b'],
      instruction = 'respond to the user. Answer any questions the user has or clarifications that could help the user',
      transition_question = 'Does the user have any more questions?',
      transition_choices = ['no', 'yes'],
      user_instruction_transitions = ['say that sounds good', 'ask another question'],
      )
```

We add a place holder transition node here so that the `intro3` and `intro3b`  odes will go to this point once they reach the transition to `start_units`

```
exec_node(
      action = 'transition',
      name = 'start_units',
      )
```


This is a good time to double check the graph of our autogram. So let's compile the graph again with


`python make_interactive_graph.py --autogram_file tutorial_examples/fractions/fraction_tutorial.py`


Viewing the updated graph it should look like this


<iframe src="../../agent_graphs/fraction_tutor/example2.html" width="100%" height="500px"></iframe>
Click on any node to see details. However over the graph and scroll to zoom in or out.


## Implementing the main loop

Each unit will use similar logic, but will have a different prompt at the first turn. Therefore, it makes sense to use a loop to implement the units. In order to do this, we need to prepare a list of initial prompts for each unit we want
```
unit_prompts=[]
#add unit for reducing fractions
unit_prompts.append(('Give a detailed description of how to reduce a fraction to its simplest form,'
'with examples. Ask the user if they have any questions so far'))

#add unit for adding fractions
unit_prompts.append(('give the user a detailed description of how to add fractions with examples,'
'including with the common denominator method (add and then reduce)'
' and the least common denominator method (find smallest denominator before adding).'
' Then ask the user if they have any questions so far.'))

#add unit for multiplying fractions
unit_prompts.append(('give the user a detailed description of how to multiply fractions, with examples.'
' Then ask the user if they have any questions so far.'))


#add unit for dividing fractions
unit_prompts.append(('give the user a detailed description of how to divide fractions, including examples.'
' Then ask the user if they have any questions.'))

```


Now we can implement the main loop that goes through the units. At each iteration, the tutor will 

1. give the material in the unit and answer any questions
2. ask practice problems
3. move onto next unit when user feels they are ready

To simplify the code, we will implement the units in a global function that we will call `do_unit()`. We will have a forloop around this function, and then proceed to the final node that congratulates the user on finishing

```
for i in range(len(unit_prompts)):
    unit_prompt = unit_prompts[i]
    do_unit()


#the final node can connect to itself to close the graph
exec_node(
      action = 'chat',
      name = 'final',
      transitions = ['final'],
      instruction = 'let the user know that we have gone through all the fraction modules and congratulate them',
      user_instruction_transitions = ['<end>'],
      )
```



Let's visualize the updated graph with the loop we have just created:


`python make_interactive_graph.py --autogram_file tutorial_examples/fractions/fraction_tutorial.py`


Viewing the updated graph it should look like this


<iframe src="../../agent_graphs/fraction_tutor/example3.html" width="100%" height="500px"></iframe>
Click on any node to see details. However over the graph and scroll to zoom in or out.

In the above graph we can see the nodes that were automatically generated to facilitate the forloop in our code.


## Implementing the do_unit() function

Now we need to make the global function `do_unit()`. We will use the function decorator `@global_function` to specify that it should be a global function. It does not need any arguments since global functions can see variables in the above scope.

The first node in global function uses the variable `unit_prompt` in it's instruction. `unit_prompt` was set in the forloop that calls this function (`unit_prompt = unit_prompts[i]`). This way the instruction will correspond to the appropriate instruction for the ith unit.

```
@global_function
def do_unit():

    exec_node(
        action = 'chat',
        name = 'step1',
        transitions = ['step2', 'step1b'],
        instruction = "$unit_prompt",
        transition_question = 'Does the user have any questions?',
        transition_choices = ['no', 'yes'],
        user_instruction_transitions = ['say that sounds good so far', 'ask a question'],
        )
```
We add a node to deal with any questions the user has
```

    exec_node(
        action = 'chat',
        name = 'step1b',
        transitions = ['step2', 'step1b'],
        instruction = 'answer any questions the user has',
        transition_question = 'Does the user have any questions?',
        transition_choices = ['no', 'yes'],
        user_instruction_transitions = ['say that sounds good so far', 'ask a question'],
        )
```
We ask the user if they are ready to begin

```
    exec_node(
        action = 'chat',
        name = 'step2',
        transitions = ['get_problem', 'step2b'],
        instruction = 'respond to the user. Ask the user if they are ready to try themself',
        transition_question = 'Is the user ready to begin?',
        transition_choices = ['yes', 'no'],
        user_instruction_transitions = ['say you are ready', 'say you have a question first'],
        )
```

We again add a node to deal with any questions the user has
```
    exec_node(
        action = 'chat',
        name = 'step2b',
        transitions = ['get_problem', 'step2b'],
        instruction = 'respond to the user',
        transition_question = 'Does the user have any more questions?',
        transition_choices = ['no', 'yes'],
        user_instruction_transitions = ['say you are ready', 'ask another question'],
        )

```
We add a placeholder node called "get_problem" for after all questions have been addressed. We call 2 functions that we will define later--make_problem() will make a problem for the user to solve, and check_answer() will get the answer to that problem in advance so that we can reference this answer later when checking if the user's answer is correct
```
    exec_node(
        action = 'transition',
        name = 'get_problem',
        )



    problem=make_problem()


    answer=check_answer(problem)

```


Now that we have created the problem and gotten the answer, we will present this problem to the user using a chat_exact node. The node below presents the exact text of the `problem` variable as the reply. We will assume 4 possible transitions--one where the user gets the answer right, one where the user get's the answer wrong, one where the user isn't sure, and one where the user asks a question.

```

    exec_node(
        action = 'chat_exact',
        name = 'present_problem',
        transitions = ['answer_correct', 'answer_wrong', 'give_hint', 'answer_prob_question'],
        instruction = '$problem',
        transition_question = 'The correct answer to the question is $answer. Which of the following is true?',
        transition_choices = ['The user gave a correct answer', 'The user gave an incorrect answer',\
        "The user wasn't sure and didn't give an answer", "The user asked a question and didn't give an answer"],
        user_instruction_transitions = ['give the correct answer', 'give a wrong answer', "say you aren't sure",\
        'ask a question about the problem without answering'],
        )
```

Let's visualize the updated graph now that we have made some progress on the do_unit() function

`python make_interactive_graph.py --autogram_file tutorial_examples/fractions/fraction_tutorial.py`


Viewing the updated graph it should look like this


<iframe src="../../agent_graphs/fraction_tutor/example4.html" width="100%" height="500px"></iframe>
Click on any node to see details. However over the graph and scroll to zoom in or out.

The function call to do_unit() is represented as a dashed edge in the graph. You should be able to zoom into this part of the graph to visualize what the function looks like so far.

We now need to make the nodes corresponding to the transitions we just defined. If the user asks a question, we will answer the question. We assume the user will either give a correct answer, give an incorrect answer, or ask another question. We reuse the node names we defined in the previous transitions--so for instance if the user answers correctly at this step we will jump to the same node as if the user answered correctly in the previous step.

```
    exec_node(
        action = 'chat',
        name = 'answer_prob_question',
        transitions = ['answer_correct', 'answer_wrong', 'answer_prob_question'],
        instruction = 'answer any questions the user has about the problem, without directly giving the answer',
        transition_question = 'The correct answer to the question is $answer. Which of the following is true?',
        transition_choices = ['The user gave a correct answer', 'The user gave an incorrect answer',\
        "The user asked a question and didn't give an answer"],
        user_instruction_transitions = ['give the correct answer', 'give a wrong answer',\
        'ask another question about what the tutor said without trying to get the answer'],
        )
```

If the user gives an incorrect answer, we explain why the users answer is wrong and ask if they want to try again. We prepare for 5 possible responses. The first 3 reuse transitions defined by other nodes the user gives a correct answer, the user gives an incorrect answer (again), the user asked a question. the last 2 are new transitions we haven't used: The user said they'd like to try again but didn't give an answer, and the user says they'd like to see the answer. 
```
    exec_node(
        action = 'chat',
        name = 'answer_wrong',
        transitions = ['answer_correct', 'answer_wrong', 'answer_prob_question', 'try_again', 'give_answer'],
        instruction = ('explain to the user why the answer is wrong without giving away the correct answer.'
        'Ask user if they would like to try again or would like to see the answer.'),
        transition_question = 'The correct answer to the question is $answer. Which of the following is true?',
        transition_choices = ['The user gave a correct answer', 'The user gave an incorrect answer',\
        "The user asked a question and didn't give an answer",\
        "The user said they'd like to try again but didn't give an answer yet",\
        'The user said they want to see the answer'],
        user_instruction_transitions = ['give the correct answer', 'give another wrong answer', 'ask a question',\
        "say you'd like to try again", "say you'd like to see the answer"],
        )
```

When the user says they aren't sure how to solve the problem ,we give a them a hint. We assume the user will either give a correct answer, incorrect answer, or ask a question
```
    exec_node(
        action = 'chat',
        name = 'give_hint',
        transitions = ['answer_correct', 'answer_wrong', 'answer_prob_question'],
        instruction = 'give the user a hint',
        transition_question = 'The correct answer to the question is $answer. Which of the following is true?',
        transition_choices = ['The correct answer to the question is $answer. The user gave a correct answer',\
        'The user gave an incorrect answer', "The user asked a question and didn't give an answer"],
        user_instruction_transitions = ['give the correct answer', 'give another wrong answer', 'ask a question'],
        )
```
Here is another visualization of the graph up to this point in the autogram:



<iframe src="../../agent_graphs/fraction_tutor/example5.html" width="100%" height="500px"></iframe>
Click on any node to see details. However over the graph and scroll to zoom in or out.


When the user asks to see the answer, we give them the answer and a detailed question. If the user has questions we answer them, otherwise we ask them another problem

```
    exec_node(
        action = 'chat',
        name = 'give_answer',
        transitions = ['get_problem', 'question_about_answer'],
        instruction = 'give the user the answer and a detailed explanation',
        transition_question = 'Did the user have any questions about the answer?',
        transition_choices = ['no', 'yes'],
        user_instruction_transitions = ['say that makes sense', 'ask a question'],
        )
```

If the user has more questions we answer them, otherwise we ask them another problem

```
    exec_node(
        action = 'chat',
        name = 'question_about_answer',
        transitions = ['get_problem', 'question_about_answer'],
        instruction = 'answer any questions the user has about the answer',
        transition_question = 'Did the user have any more questions?',
        transition_choices = ['no', 'yes'],
        user_instruction_transitions = ['say that makes sense', 'ask a question'],
        )
```

This node is for the earlier transition where the user said they would like to try again, but didn't give a new answer. 
```
    exec_node(
        action = 'chat',
        name = 'try_again',
        transitions = ['answer_correct', 'answer_wrong', 'answer_prob_question'],
        instruction = 'respond to the user',
        transition_question = 'The correct answer to the question is $answer. Which of the following is true?',
        transition_choices = ['The user gave a correct answer', 'The user gave an incorrect answer',\
        "The user asked a question and didn't give an answer"],
        user_instruction_transitions = ['give the correct answer', 'give another wrong answer', 'ask a question'],
        )
```

When the user gets the answer correct, we ask them if they would like to try another problem or move onto another unit. If the user wants to move on, we return from the do_unit() function which will iterate in the earlier forloop and proceed tot he next unit. Otherwise we will go back to get_problem, which will create another problem for them to solve.
```
    exec_node(
        action = 'chat',
        name = 'answer_correct',
        transitions = ['get_problem', 'return'],
        instruction = ('Tell the user the answer is correct, and talk about the answer in more detail.'
        ' Ask the user if they would like to try a new problem or move onto the next unit'),
        transition_question = 'Which would the user prefer?',
        transition_choices = ['Try another problem', 'Move onto the next unit'],
        user_instruction_transitions = ['say you would like to try another', 'say you are ready to move on'],
        )

```

Here is another visualization of the graph up to this point in the autogram:



<iframe src="../../agent_graphs/fraction_tutor/example6.html" width="100%" height="500px"></iframe>
Click on any node to see details. However over the graph and scroll to zoom in or out.

## Implementing other functions

Now the only thing remaining is for us to define the make_problem() and check_answer() functions we called but didn't define yet. We make get_problem() a regular function using @function. We want get_problem to be able to see the past conversation to know what the unit is, but we don't want to permanently update the conversation with this thought, since it could extra text/noise into the prompt. a regular function accomplishes this


```
@function
def make_problem():
    problem= exec_node(
        action = 'thought',
        instruction = 'Write a new problem for the user to solve that tests their understanding of the material.'
        )
    return problem


```

We can make check_answer() local function since everything the model needs to know to get the answer should be included in the problem, which we passed as an argument and can use in the instruction using $syntax.
```
@local_function
def check_answer(problem):
    answer = exec_node(
        action = 'thought',
        instruction = 'consider the problem $problem . Reply with the answer to the problem and nothing else.'
        )
    return answer

```

## Visualizing and testing the full autogram

Here is the visualization of the full autogram now that we have finished.



<iframe src="../../agent_graphs/fraction_tutor/example7.html" width="100%" height="500px"></iframe>
Click on any node to see details. However over the graph and scroll to zoom in or out.

You can compile the graph yourself `python make_interactive_graph.py --autogram_file tutorial_examples/fractions/fraction_tutorial.py`.

Now that you have created the autogram, you can converse with it using 

`python run_autograms.py --api_key_file api_keys.json --autogram_file tutorial_examples/fractions/fraction_tutorial.py --interactive`


Alternatively, you can use the code below to save visualizations and converse with the autogram

```
from autograms.graph_utils import visualize_autogram
from autograms import read_autogram
import json

API_KEY_FILE = "api_keys.json"
with open(API_KEY_FILE) as f:
      api_keys = json.load(f)


autogram = read_autogram("tutorial_examples/fractions/fraction_tutorial.py",api_keys=api_keys)

visualize_autogram(autogram,root_path="tutorial_examples/fractions/fraction_tutorial")

memory_object=None
user_reply=""
while True:
      reply,memory_object = autogram.reply(user_reply,memory_object=memory_object)
      print("Agent: " + reply)
      user_reply = input("User: ")

```

This tutorial covered many features of AutoGRAMS, including both types of variable references, all 3 types of AutoGRAMS functions, and python-style loops wrapped around complex graph logic. If you can understand this example well you should be ready to start making your own advanced autograms!


