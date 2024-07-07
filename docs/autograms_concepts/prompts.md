# Prompt formation

This section describes how prompts are formed in AutoGRAMS


## prompt formation for chatbot

Chatbots in AutoGRAMS take in a list of input turns (corresponding to user turns or instructions), a list of output turns (corresponding to assistant turns/model outputs), as well as an optional prefix for how the reply should start (for internal models only).


When preparing the prompt to get a new chatbot output at either a thought node or a chat node, the autogram re-iterates over past turns to get these input and output turns.


For every previously visited node that is within the current scope (depending functions and function types if used), if that node is a thought node or a chat node, it adds a turn to the conversation history that the chatbot sees. the inputs and outputs are determined as follows:

for each past thought or chat node visited:

    - if it is a thought node
        - if the thought node came immediately after a user reply, then both the instruction and user reply will appear in the input for that turn

        -otherwise, only the instruction will appear in the input for that turn

    - if it is a chat node 
        - if the chat node came immediately after a user reply, then only user reply will appear in the input for that turn. The old instruction is discarded for chat nodes to avoid long prompts. We may later add an option to retain chat instructions in the autogram config


        - otherwise,the chat node's instruction will appear in the input for that turn

The initial prompt set by "set_prompt" and "append_prompt" actions, or by the AutogramConfig prompt, is preappended to the first input.

For the last input, corresponding to the end of the prompt, the string is determined by the instruction template. The default instruction template is "\<last_response\>\n\nInstruction for \<agent_name\>: \<instruction\>", where\<last_response\>, \<agent_name\>, and \<instruction\> are special place holder tokens for the instruction, agent name, and last response. Sometimes the last response will be the empty string if the last user response is already in one of the past inputs (which will happen if there is at least 1 thought node before replying with a chat node).

Lastly, replies have a reply start, which is "Agent's reply:" if the default start template and agent name are used. Depending on whether the start type is suffix or prefix, the reply start either appears at the end of the last input, or at the start of the model's reply (only possible for models running locally). 



