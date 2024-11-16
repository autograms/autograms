from autograms import autograms_function
from autograms.nodes import reply, reply_instruction, thought, silent_thought
from autograms.functional import set_system_prompt, multiple_choice, yes_or_no, generate_list, generate_fixed_list, generate_fixed_dict

# Initial message to introduce the chatbot and its functionality
intro_message = (
    "Hi. My name is Ava and I'm an AI math tutor for beginner math. "
    "I can create a mini-course for you and come up with practice problems for you to work through. "
    "Let me know what subject you want to study first."
)

@autograms_function()
def chatbot():
    # Set a system prompt to define the AI's role and behavior
    set_system_prompt(
        "You are an AI tutor for beginner math (algebra and below). "
        "Follow all instructions carefully, ensure user understanding before proceeding, "
        "and avoid adding extra content that may disrupt the conversation flow."
    )

    # Start the interaction with the introduction message
    reply(intro_message)

    chosen = False
    while not chosen:
        # Ask the AI to decide what the user’s chosen subject is
        answer_idx = multiple_choice(
            "Which of the following is true?",
            choices=[
                "the user picked a beginner math subject",
                "the user picked an advanced math subject",
                "the user picked a non-math subject",
                "the user didn't pick a subject"
            ]
        )

        if answer_idx == 0:  # Beginner math subject
            chosen = True

        elif answer_idx == 1:  # Advanced subject
            reply_instruction(
                "Warn the user that the subject is advanced and might be challenging for this tutor. "
                "Ask if they want to proceed or pick an easier subject."
            )
            answer_idx = multiple_choice(
                "Which does the user prefer?",
                choices=["proceed with the original subject", "choose a different subject"]
            )
            if answer_idx == 0:
                chosen = True  # Proceed with the advanced subject

        elif answer_idx == 2:  # Non-math subject
            reply_instruction("Tell the user that only math subjects are supported.")

        elif answer_idx == 3:  # No subject chosen
            reply_instruction(
                "Answer any questions the user has. If relevant, describe beginner math topics "
                "and ask the user to choose one."
            )

    approved = False
    while not approved:
        # Generate a list of unit topics based on the chosen subject
        unit_list = generate_list("Write a list of beginner math concepts for the chosen subject.")

        # Generate teaching prompts for each unit
        unit_dict = generate_fixed_dict(
            "For each concept, write a teaching prompt.",
            unit_list
        )
        unit_prompts = list(unit_dict.values())

        # Present the proposed course structure to the user
        course_str = "\n\n".join(unit_list)
        reply_instruction(
            f"We propose the following course units:\n\n{course_str}\n\n"
            "Summarize the plan and ask the user for feedback."
        )

        answer_idx = multiple_choice(
            "Is the user okay with the proposed material or would they prefer refinements?",
            ["they are fine with the material", "they prefer refinements"]
        )

        if answer_idx == 0:
            approved = True  # User approves the course structure

    # Introduce the overall subject
    reply_instruction("Introduce the chosen subject at a high level.")
    address_questions()

    # Teach each unit
    for prompt in unit_prompts:
        do_unit(prompt)

    # End state: Keep responding in an infinite loop
    while True:
        reply_instruction(
            "Let the user know the course is complete and congratulate them on their progress."
        )

@autograms_function()
def address_questions(max_turns=3):
    total_turns = 0

    # Handle user questions up to a maximum number of turns
    while yes_or_no("Did the user ask a question?"):
        reply_instruction("Answer any user questions or provide clarifications.")
        total_turns += 1
        if total_turns == max_turns:
            break

@autograms_function()
def do_unit(unit_prompt):
    # Teach the current unit and respond to the user
    reply_instruction(unit_prompt)
    address_questions()

    reply_instruction("Ask the user if they are ready to practice.")
    if not yes_or_no('Is the user ready to start solving problems?'):
        address_questions()

    while True:
        # Generate a problem and its answer
        problem = silent_thought("Create a practice problem based on the current unit.")
        answer = silent_thought(f"Provide the solution for the problem: {problem}")

        reply(problem)

        # Track the user's attempts to answer the problem
        max_non_answer_tries = 0
        max_answer_tries = 3
        hint_threshold = 2
        total_answer_tries = 0
        total_non_answer_tries = 0
        user_correct_answer = False
        user_answered = False

        while not user_correct_answer:
            if user_answered:
                # Check if the user’s answer is correct
                user_correct_answer = yes_or_no(
                    f"The correct answer is {answer}. Did the user give the right answer?"
                )
                if not user_correct_answer:
                    total_answer_tries += 1
                    if total_answer_tries == hint_threshold:
                        reply_instruction(
                            "Tell the user their answer is incorrect and provide a hint."
                        )
                    elif total_answer_tries == max_answer_tries:
                        break
                    else:
                        reply_instruction(
                            "Explain why the user's answer is incorrect, but don't provide the correct answer yet."
                        )
                    user_answered = False
            else:
                # Check if the user has provided an answer
                user_answered = yes_or_no("Did the user provide an answer?")
                if not user_answered:
                    total_non_answer_tries += 1
                    if total_non_answer_tries == max_non_answer_tries:
                        break
                    else:
                        reply_instruction("Answer any additional questions the user has.")

        if user_correct_answer:
            reply_instruction("Congratulate the user on solving the problem.")
        else:
            reply_instruction(
                f"The correct answer was {answer}. Explain the solution in detail."
            )

        address_questions()

        # Check if the user wants to try another problem or move on
        if not yes_or_no("Does the user want to try another problem?"):
            reply_instruction("Ask the user if they want another problem or to move on.")
            answer_idx = multiple_choice(
                "What does the user prefer?",
                ["try another problem", "move to the next unit"]
            )

            if answer_idx == 1:
                break  # Move on to the next unit
