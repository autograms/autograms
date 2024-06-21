exec_node(
      action = 'set_prompt',
      name = 'start1',
      instruction = 'You are tutor for the subject of fractions. Your goal is to teach the student what fractions are, as well as how to reduce, add, multiply and divide fractions. Follow all instructions and be sure to make sure the user understands before continuing with each step.',
      )

exec_node(
      action = 'set_user_prompt',
      name = 'start2',
      instruction = 'You are a student (the user) trying to learn the subject of fractions from a teacher.',
      )

exec_node(
      action = 'chat',
      name = 'intro',
      instruction = 'Introduce yourself as a tutor named fractobot. Ask the user how they are and how much they have previously learned about the subject',
      user_instruction_transitions = ["tell the tutor you don't know much about it but are excited to learn"],
      )

exec_node(
      action = 'chat',
      name = 'intro2',
      transitions = ['intro3', 'intro2b'],
      instruction = 'respond to the user and ask if they are ready to begin',
      transition_question = 'Does the user have any questions yet?',
      transition_choices = ['no', 'yes'],
      user_instruction_transitions = ['say you are ready', 'say that before you begin you have a question, and ask the question'],
      )

exec_node(
      action = 'chat',
      name = 'intro2b',
      transitions = ['intro3', 'intro2b'],
      instruction = 'respond to the user',
      transition_question = 'Does the user have any more questions?',
      transition_choices = ['no', 'yes'],
      user_instruction_transitions = ['say you are ready now', 'ask another question'],
      )


exec_node(
      action = 'chat',
      name = 'intro3',
      transitions = ['start_units', 'intro3b'],
      instruction = 'describe what a fraction is at a high level, adding on to anything the user has previously said. Ask the user if they have any questions',
      transition_question = 'Does the user have any questions?',
      transition_choices = ['no', 'yes'],
      user_instruction_transitions = ['say that sounds good so far', 'ask a question'],
      )

exec_node(
      action = 'chat',
      name = 'intro3b',
      transitions = ['start_units', 'intro3b'],
      instruction = 'respond to the user. Answer any questions the user has or clarifications that could help the user',
      transition_question = 'Does the user have any more questions?',
      transition_choices = ['no', 'yes'],
      user_instruction_transitions = ['say that sounds good', 'ask another question'],
      )

exec_node(
      action = 'transition',
      name = 'start_units',
      )


unit_prompts=[]
#add unit for reducing fractions
unit_prompts.append("Give a detailed description of how to reduce a fraction to its simplest form, with examples. Ask the user if they have any questions so far")

#add unit for adding fractions
unit_prompts.append("give the user a detailed description of how to add fractions with examples, including with the common denominator method (add and then reduce) and the least common denominator method (find smallest denominator before adding). then ask the user if they have any questions so far.")

#add unit for multiplying fractions
unit_prompts.append("give the user a detailed description of how to multiply fractions, with examples. Then ask the user if they have any questions so far.")


#add unit for dividing fractions
unit_prompts.append("give the user a detailed description of how to divide fractions, including examples. then ask the user if they have any questions.")

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
    
    exec_node(
        action = 'chat',
        name = 'step1b',
        transitions = ['step2', 'step1b'],
        instruction = 'answer any questions the user has',
        transition_question = 'Does the user have any questions?',
        transition_choices = ['no', 'yes'],
        user_instruction_transitions = ['say that sounds good so far', 'ask a question'],
        )
    
    exec_node(
        action = 'chat',
        name = 'step2',
        transitions = ['get_problem', 'step2b'],
        instruction = 'respond to the user. Ask the user if they are ready to try themself',
        transition_question = 'Is the user ready to begin?',
        transition_choices = ['yes', 'no'],
        user_instruction_transitions = ['say you are ready', 'say you have a question first'],
        )
    exec_node(
        action = 'chat',
        name = 'step2b',
        transitions = ['get_problem', 'step2b'],
        instruction = 'respond to the user',
        transition_question = 'Does the user have any more questions?',
        transition_choices = ['no', 'yes'],
        user_instruction_transitions = ['say you are ready', 'ask another question'],
    )
    exec_node(
        action = 'transition',
        name = 'get_problem',
        )



    problem=make_problem()


    answer=check_answer(problem)


    exec_node(
        action = 'chat_exact',
        name = 'present_problem',
        transitions = ['answer_correct', 'answer_wrong', 'give_hint', 'answer_prob_question'],
        instruction = '$problem',
        transition_question = 'The correct answer to the question is $answer. Which of the following is true?',
        transition_choices = ['The user gave a correct anwer', 'The user gave an incorrect answer', "The user wasn't sure and didn't give an answer", "The user asked a question and didn't give an answer"],
        user_instruction_transitions = ['give the correct answer', 'give a wrong answer', "say you aren't sure", 'ask a question about the problem without answering'],
        )
    
    exec_node(
        action = 'chat',
        name = 'answer_prob_question',
        transitions = ['answer_correct', 'answer_wrong', 'answer_prob_question'],
        instruction = 'answer any questions the user has about the problem, without directly giving the answer',
        transition_question = 'The correct answer to the question is $answer. Which of the following is true?',
        transition_choices = ['The user gave a correct anwer', 'The user gave an incorrect answer', "The user asked a question and didn't give an answer"],
        user_instruction_transitions = ['give the correct answer', 'give a wrong answer', 'ask another question about what the tutor said without trying to get the anwer'],
        )
    exec_node(
        action = 'chat',
        name = 'answer_wrong',
        transitions = ['answer_correct', 'answer_wrong', 'answer_prob_question', 'try_again', 'give_answer'],
        instruction = 'explain to the user why the answer is wrong without giving away the correct answer. Ask user if they would like to try again or would like to see the answer.',
        transition_question = 'The correct answer to the question is $answer.Which of the following is true?',
        transition_choices = ['The user gave a correct anwer', 'The user gave an incorrect answer', "The user asked a question and didn't give an answer", "The user said they'd like to try again but didn't give an answer yet", 'The user said they want to see the answer'],
        user_instruction_transitions = ['give the correct answer', 'give another wrong answer', 'ask a question', "say you'd like to try again", "say you'd like to see the answer"],
        )
    exec_node(
        action = 'chat',
        name = 'give_hint',
        transitions = ['answer_correct', 'answer_wrong', 'answer_prob_question'],
        instruction = 'give the user a hint',
        transition_question = 'The correct answer to the question is $answer. Which of the following is true?',
        transition_choices = ['The correct answer to the question is $answer. The user gave a correct anwer', 'The user gave an incorrect answer', "The user asked a question and didn't give an answer"],
        user_instruction_transitions = ['give the correct answer', 'give another wrong answer', 'ask a question'],
        )

    exec_node(
        action = 'chat',
        name = 'give_answer',
        transitions = ['get_problem', 'question_about_answer'],
        instruction = 'give the user the answer and a detailed explanation',
        transition_question = 'Did the user have any questions about the answer?',
        transition_choices = ['no', 'yes'],
        user_instruction_transitions = ['say that makes sense', 'ask a question'],
        )
    exec_node(
        action = 'chat',
        name = 'question_about_answer',
        transitions = ['get_problem', 'question_about_answer'],
        instruction = 'answer any questions the user has about the answer',
        transition_question = 'Did the user have any more questions?',
        transition_choices = ['no', 'yes'],
        user_instruction_transitions = ['say that makes sense', 'ask a question'],
        )
    
    exec_node(
        action = 'chat',
        name = 'try_again',
        transitions = ['answer_correct', 'answer_wrong', 'answer_prob_question'],
        instruction = 'respond to the user',
        transition_question = 'The correct answer to the question is $answer. Which of the following is true?',
        transition_choices = ['The user gave a correct anwer', 'The user gave an incorrect answer', "The user asked a question and didn't give an answer"],
        user_instruction_transitions = ['give the correct answer', 'give another wrong answer', 'ask a question'],
        )
    
    exec_node(
        action = 'chat',
        name = 'answer_correct',
        transitions = ['get_problem', 'return'],
        instruction = 'Tell the user the answer is correct, and talk about the answer in more detail. Ask the user if they would like to try a new problem or move onto the next unit',
        transition_question = 'Which would the user prefer?',
        transition_choices = ['Try another problem', 'Move onto the next unit'],
        user_instruction_transitions = ['say you would like to try another', 'say you are ready to move on'],
        )
    
@function
def make_problem():
    problem= exec_node(
        action = 'thought',
        instruction = 'Write a new problem for the user to solve that tests their understanding of the material.'
        )
    return problem


@local_function
def check_answer(problem):
    answer = exec_node(
        action = 'thought',
        instruction = 'consider the problem $problem . Reply with the answer to the problem and nothing else.'
        )
    return answer
