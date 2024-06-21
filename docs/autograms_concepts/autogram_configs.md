# Autogram configs


The AutogramConfig Class is important for controlling settings of the autogram, including many settings that can't currently be set from inside the program. Some important choices are setting the models to be used, setting the prompt templates, and setting the python imports and APIs that will be visible from the lmsheets code.


## Controlling the python imports

Autogram configs allow you to set what python functions and APIs will be visible from the scope of the autogram. 3 arguments for initializing the autogram config control this. 


`python_builtins` set what python built ins are available. All other python built ins are disabled. By default, python built ins that allow imports or system manipulation are disabled. To allow all built ins, you can pass `dir(globals()['__builtins__'])` as this argument

`python_imports` this arguments allows you to specify imports by string. For instance passing `["numpy"]` will import the module numpy so that it is usable from within an autogram

`python_modules` you can pass any python function or module to the autogram config to make it usable. 

If you'd like to pass a function that requires an API key, include a keyword argument called "api_key" in the function you pass. (Or wrap the function you'd like to use with another function that includes this argument and handles the api key appropriately).
You will also need to include the api key in your `api_keys.json` file--the key should match the name of the function, and the value should match the api key.



## Setting the models

An autogram uses 3 models A chatbot, a classifier and a userbot (used to simulate user). These models can be set to an API, or a huggingface model running locally on your machine. The userbot and chatbot currently use the same model, while the classifier has the option of using a different model. Use the following arguments to AutogramConfig to specify the chatbot and classifier.


`chatbot_type` - currently accepts "openai" or "huggingface"
`chatbot_path`
    - If huggingface, should be the huggingface path or local path to huggingface model. 
    - If openai, should be Open AI chat completion model you want to use
`classifier_type` - currently accepts "openai" or "huggingface"

`classifier_path`
    - If huggingface, should be the huggingface path or local path to huggingface model. Will reuse model if path is the same as chatbot
    - If openai, should be Open AI chat completion model you want to use


## Controlling generations


`max_response_len`

    max response length from the model. If you have longer templated responses, you can still use `chat_exact` or `chat_suffix` actions to generate longer replies

`chatbot_generation_args`

    A dictionary of generation arguments for the model

`banned_phrases`

    If model attempts to generate banned phrases, it will attempt to generate again by penalizing previous response. Most useful for when OpenAI refuses to respond (e.x.: Sorry, as a language model I am unable to do that)





## Setting prompts and prompt templates

`default_prompt` 
    default starting prompt for chatbot that appears before any conversational turns. Every new function call reinitializes to default prompt

`default_user_prompt` 
    default starting prompt for userbot. Every new function call reinitializes to default user prompt

`agent_name` 
    name of agent in the turn-wise prompts

`user_name` 
    name of user in the turn-wise prompts

`instruction_name` 
    name of instruction in the turn-wise prompt, 

`default_question_prompt`
    prompt given before the transition_question question for classifier bot, can be overriden by question_prompt setting at each node

`default_transition_context` 
    number of turns of context used for predicting transitions

`instruction_template` 
    Uses special tokens \<last_response\>, \<agent_name\>, and \<instruction\> . Controls how turn wise instructions appear in the prompt, relative to the last response and agent name. default is
    "\<last_response\>\n\nInstruction for \<agent_name\>: \<instruction\>"

`user_instruction_template`
    instruction template for user simulations


`reply_start_template` 
    controls the very final part of the prompt that start's the agent's reply. Default is \<agent_name\>'s reply


`reply_start_type`
    Should the reply start appear at the end of the last turn (reply_start_type="suffix") or beginning of the model's turn "prefix". Prefix is only supported for huggingface models. For chat completion model behind at api it isn't possible to control this.




## All other arguments

    

`error_response` -- response if chatbot has error

`chatbot_max_tries` -- max tries for chatbot

`chatbot_wait_per_try` -- number of seconds to wait between tries for chatbot

`classifier_max_tries` -- max tries for classifier

`classifier_wait_per_try` -- number of seconds to wait between tries for classifier

`banned_phrases` -- phrases we try to strongly discourage chatbot from generating, usually corresponding to refusal to follow 
instruction.

`post_process_response` -- apply post processing to response

`log_model_turns` -- log model turns in MemoryObject

`start_state` -- default start state

`end_signal` -- text signaling finish during user simulation

`default_transition_context` -- number of turns of context for predicting transitions

`interjection_question` -- question to ask for predicting interjections

`interjection_default_answer` -- default answer that leads to no interjection, usually meaning that none of the interjection conditions are true

`default_probability_interjection` -- probability of simulating each interjection state

`default_primary_prob_delta` -- how much more likely should first (default) transition be than all other transitions, which are uniform

        