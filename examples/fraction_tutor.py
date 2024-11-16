from autograms import autograms_function
from autograms.nodes import reply, reply_instruction, thought, silent_thought
from autograms.functional import set_system_prompt, multiple_choice, yes_or_no, generate_list, generate_fixed_list, generate_fixed_dict

# Introduction message for the user
intro_message = "Hi. my name is fractobot. I am here to teach you the basics of fractions, are you ready to start?"

# Prepare a list of prompts for each unit in the fraction tutorial
unit_prompts = []

# Add a unit for reducing fractions
unit_prompts.append("Give a detailed description of how to reduce a fraction to its simplest form, with examples. Ask the user if they have any questions so far")

# Add a unit for adding fractions
unit_prompts.append("Give the user a detailed description of how to add fractions with examples, including with the common denominator method (add and then reduce) and the least common denominator method (find smallest denominator before adding). Then ask the user if they have any questions so far.")

# Add a unit for multiplying fractions
unit_prompts.append("Give the user a detailed description of how to multiply fractions, with examples. Then ask the user if they have any questions so far.")

# Add a unit for dividing fractions
unit_prompts.append("Give the user a detailed description of how to divide fractions, including examples. Then ask the user if they have any questions.")

@autograms_function()
def chatbot():
    # Set up the system prompt to guide the chatbot's overall behavior
    set_system_prompt("You are a tutor for the subject of fractions. Your goal is to teach the student what fractions are, as well as how to reduce, add, multiply, and divide fractions. Ensure the user understands each step before continuing.")


    # Start the conversation with an introduction
    reply(intro_message)

    # Ask the user if they're ready to begin
    if not yes_or_no("Is the user ready to begin?"):
        # If the user isn't ready, provide an opportunity for questions
        reply_instruction("Answer any additional questions the user has.")

    # Explain what a fraction is
    reply_instruction('Describe what a fraction is at a high level. Ask the user if they have any questions.')
    # Address any questions the user may have
    address_questions()

    # Go through each unit in the list
    for i in range(len(unit_prompts)):
        do_unit(unit_prompts[i])

    # End state: infinite loop for continued user interaction
    while True:
        reply_instruction('Let the user know we have completed all the fraction modules and congratulate them.')

@autograms_function()
def address_questions(max_turns=3):
    total_turns = 0
  
    # Loop to handle user questions up to a maximum number of turns
    while yes_or_no("Did the user explicitly ask a question in their last response?"):
        reply_instruction('Respond to the user. Answer any questions or provide clarifications.')
        total_turns += 1
        if total_turns == max_turns:
            break

@autograms_function()
def do_unit(unit_prompt):
    # Present the unit prompt and handle the user's response
    reply_instruction(unit_prompt)
    address_questions()

    # Ask if the user is ready to practice
    reply_instruction("Respond to the user, ask if they are ready to try themselves.")
    if not yes_or_no('Is the user ready to begin?'):
        address_questions()

    while True:
        # Generate a problem and its answer
        problem = silent_thought("Write a new problem for the user to solve.")
        answer = silent_thought(f"Consider the problem {problem}. Provide the answer.")

        reply(problem)

        # Handle user attempts at solving the problem
        max_non_answer_tries = 0
        max_answer_tries = 3
        hint_threshold = 2
        total_answer_tries = 0
        total_non_answer_tries = 0
        user_correct_answer = False
        user_answered = False

        while not user_correct_answer:
            if user_answered:
                # Check if the user's answer matches the correct answer
                user_correct_answer = yes_or_no(f"The correct answer is {answer}. Did the user's answer match?")
                if not user_correct_answer:
                    total_answer_tries += 1
                    # Provide feedback based on the number of attempts
                    if total_answer_tries == hint_threshold:
                        reply_instruction("Let the user know the answer is incorrect and provide a hint.")
                    elif total_answer_tries == max_answer_tries:
                        break
                    else:
                        reply_instruction("Explain why the answer is incorrect, but do not provide the correct answer yet.")
                    user_answered = False
            else:
                user_answered = yes_or_no("Did the user provide their answer to the problem?")
                if not user_answered:
                    total_non_answer_tries += 1
                    if total_non_answer_tries == max_non_answer_tries:
                        break
                    else:
                        reply_instruction("Answer any questions the user has.")

        if user_correct_answer:
            reply_instruction("Congratulate the user on the correct answer and comment on their understanding.")
        else:
            reply_instruction(f"The correct answer was {answer}. Explain it in detail and address any gaps in understanding.")
            
        address_questions()

        # Ask if the user wants to try another problem or move on
        reply_instruction("Ask the user if they would like to try another problem or move on.")
        answer_idx = multiple_choice("What would the user prefer?", choices=["Try another problem", "Move on to another unit"])

        if answer_idx == 0:
            continue  # User wants another problem
        else:
            break  # Move on to the next unit
