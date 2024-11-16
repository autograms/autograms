from autograms.nodes import reply, reply_instruction
from autograms.functional import yes_or_no
from autograms import autograms_function

#this decorator allows the function to have special behavior such as temporarily returning replies
@autograms_function()
def chatbot():

    #model goes first here, we have a fixed introductory message. Pauses program and returns a reply
    reply("Would you like me to tell you more about the latest advances in AI?", ADDRESS="ask_question")
    #program will continue from this point after first user reply 

    #The agent decides whether it thinks the user wants to talk about AI based on their response  
    user_wants_ai = yes_or_no("does the user want to talk about AI?")

    if user_wants_ai:
        #pause and save program and return a reply based on instruction below    
        reply_instruction(
            "Tell the user about the latest advances in AI. Mention that "
            "a new framework called AutoGRAMS was recently released that allows greater control over AI agents.",
            ADDRESS="tell_about_ai"
        )
        #continue program here after user response

    else:
         #pause and save program and return a reply based on instruction below  
        reply_instruction(
            "Confirm with the user what they would prefer to talk about.",
            ADDRESS="ask_preference"
        )
        #continue program here after user response

    #infinite while loop continues conversation as long as user keeps responding
    while True:
        #pause and save program and output reply based on instruction below
        reply_instruction("Respond to the user.", ADDRESS="continue_conversation")
        #continue program here after user response

