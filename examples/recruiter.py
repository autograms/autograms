from autograms import autograms_function
from autograms.nodes import reply, reply_instruction, thought, silent_thought
from autograms.functional import set_system_prompt, multiple_choice, yes_or_no

# Predefined salary range for the position
salary_range = "150k-180k"

@autograms_function()
def chatbot():
    # Set the system prompt to define the AI's role as a recruiter.
    set_system_prompt(
        'You are Daisy, a recruiter in the HR department of Dipply, a medium-sized biotech company. '
        'Your goal is to interact with candidates who have applied for jobs and ask them routine questions. '
        'Start the conversation by introducing yourself and thank the person for taking the time to talk to you.'
    )

    user_ready = False

    # Ensure the user is ready to proceed with the interview.
    while not user_ready:
        reply_instruction("Ask the user if they are ready to begin.")
        user_ready = yes_or_no("Is the user ready to proceed?")

    # Gather background information from the user.
    reply_instruction("Ask the user to describe their background in detail, including relevant experience.")
    reply_instruction("Respond to the user and ask another question about their relevant background.")
    reply_instruction(
        "Respond to the user and ask another detailed question about a specific aspect of their background."
    )

    # Transition to salary expectations.
    reply_instruction(
        "Respond to the user. Then move on and ask the candidate about their salary expectations for the position."
    )

    # Determine the user's response regarding salary expectations.
    answer_idx = multiple_choice(
        "I need you to answer a multiple-choice question to determine the user's intent. "
        "Either they:\n"
        "A. Asked a question about salary expectations\n"
        "B. Avoided the question\n"
        "C. Specified a salary range.\n\n"
        "Examples:\n"
        "A: What is the budgeted salary range for this position?\n"
        "B: I don't really care about salary; what's important is team fit and company vision.\n"
        "C: My expectations are in line with market standards, around 150k.",
        choices=[
            'the user asked about the salary range',
            "the user avoided the question or said they didn't know",
            'the user specified a salary range or number'
        ]
    )

    gave_range = False

    # Handle each response type regarding salary.
    if answer_idx == 0:
        # User asked about the salary range
        reply_instruction(
            f"Respond to the user. State our salary range as {salary_range}, depending on the candidate. "
            "Ask if this would be acceptable."
        )
    elif answer_idx == 1:
        # User avoided the question or was unsure
        reply_instruction(
            "Respond to the user. Ask if they can be more specific about their desired salary, "
            "so we can ensure expectations align with our budget."
        )
        gave_range = yes_or_no("Did the user provide a specific salary range?")
        if not gave_range:
            # User still didn't specify, provide the company's salary range
            reply_instruction(
                f"Respond to the user. State our salary range as {salary_range}, depending on the candidate. "
                "Ask if this is acceptable."
            )
    else:
        # User provided a salary range directly
        gave_range = True

    exp_okay = False

    if gave_range:
        # Check if the user's salary expectations are within the defined range.
        if yes_or_no(f"Is the user's salary range {salary_range} or less?"):
            exp_okay = True
        else:
            reply_instruction(
                f"Inform the user that the salary range for this position is {salary_range}. "
                "Ask if this is acceptable."
            )

    # If expectations were not within the range, check if the user is open to negotiation.
    if not exp_okay:
        if yes_or_no("Is the user open to the salary range for the position?"):
            exp_okay = True
        else:
            exp_okay = False

    # Finalize based on salary expectations.
    if exp_okay:
        reply_instruction("Tell the user that's great and that we will be in touch with the next steps.")
    else:
        reply_instruction("Tell the user that's unfortunate and wish them the best.")

    # End conversation with a polite closing statement in an infinite loop.
    while True:
        reply("This conversation is now over. Thank you for your time.")
