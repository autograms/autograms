




LAST_RESPONSE_TOKEN="<last_response>"
INSTRUCTION_TOKEN="<instruction>"
AGENT_NAME_TOKEN="<agent_name>"


BANNED_PHRASES=["that request","language model","provide a response","I can't respond","I cannot engage","I can't engage","I'm sorry, I can't","I'm sorry, I cannot","I cannot respond","I can't provide","I cannot provide","I can't fullful","I cannot fullfill","that prompt","that instruction","open ai"]
CHATBOT_GENERATION_ARGS={"temperature":0.7,"batch_size":1}
ERROR_RESPONSE="Sorry, the system is down right now. Hopefully the system will be back soon and you can continue your conversation."
INSTRUCTION_TEMPLATE=LAST_RESPONSE_TOKEN+"\n\nInstruction for "+AGENT_NAME_TOKEN+ ": " +INSTRUCTION_TOKEN
DEFAULT_QUESTION_PROMPT="I need you to solve a multiple choice question.\n"

#USER_INSTRUCTION_TEMPLATE=LAST_RESPONSE_TOKEN+"\n\nInstruction for user: "+INSTRUCTION_TOKEN
DEFAULT_REPLY_START_TEMPLATE=AGENT_NAME_TOKEN+ "'s reply:"



# INTERJECTION_QUESTION="Which of the following is True?"

# INTERJECTION_DEFAULT_ANSWER="None of the above."

# PYTHON_BUILT_INS=["int","float","complex","list","tuple","range","dict","bytes", "bytearray","set","frozenset","str","sum","pow","abs","max","min","len","ord","chr","reversed","map","zip","type","print"]
# PYTHON_IMPORTS=["import math","import operator","import functools","import ast"]

ALLOWED_REPLY_START_TYPES=["suffix","prefix","none"]


#CHAT_EXACT_INST_CONVERSION="Reply to the user with the following text: "+INSTRUCTION_TOKEN 
#THOUGHT_EXACT_INST_CONVERSION="Reply with this exact text: " +INSTRUCTION_TOKEN 
REPLY_SUFFIX_INST_CONVERSION="Respond to the user's last reply, and then include the **bold** text at the end of your response to direct the conversation:**" + INSTRUCTION_TOKEN  +"**. It is also okay for the whole response to be the bold text if it fits the situation."


    
class AutogramConfig():
    def __init__(
            self,
            max_response_len=1024,
            default_prompt="You are an agent.",
            agent_name="Agent",
            user_name="User",
            instruction_name="Instruction",
            chatbot_type = "openai",
            chatbot_path="gpt-4o",
            system_prompt_in_turns=False,
            error_response=None,
            chatbot_generation_args=None, 
            chatbot_max_tries=3,
            chatbot_wait_per_try=5,
            chatbot_max_input_len=3500,
            classifier_max_tries=2,
            classifier_wait_per_try=5,
            classifier_max_input_len=2048,
            banned_phrases=None,
            post_process_response=True,
            classifier_type="openai",
            classifier_path="gpt-4o",
            instruction_template=None,
            reply_start_type="suffix",
            default_reply_start_template=None,
            user_instruction_template=None,
            default_question_prompt=None,
            default_transition_context=1,
            reply_suffix_inst_conversion=None,

        ):

        """
Initialize the configuration object for AutoGRAMS.

This class provides a flexible way to configure various aspects of AutoGRAMS, including which models are used,
how prompts are generated, system retries, and instruction templates.

Parameters:
    max_response_len: Maximum response length from the model in tokens.
    default_prompt: Starting prompt for the agent.
    agent_name: Name of the agent, used in prompt templates.
    user_name: Name of the user, used in prompt templates.
    instruction_name: Label for the instruction token in prompts.
    chatbot_type: Type of chatbot, e.g., "openai"
    chatbot_path: Model path or API endpoint for the chatbot.
    system_prompt_in_turns: Whether to include the system prompt in the first user turn instead of as separate system prompt
    error_response: Fallback response when the chatbot encounters an error.
    chatbot_generation_args: Arguments for chatbot generation (e.g., temperature, batch size).
    chatbot_max_tries: Maximum number of retries for chatbot requests in case of failure.
    chatbot_wait_per_try: Number of seconds to wait between retries for chatbot requests.
    chatbot_max_input_len: Maximum allowable input length for chatbot prompts in tokens.
    classifier_max_tries: Maximum number of retries for classifiers in case of failure.
    classifier_wait_per_try: Number of seconds to wait between retries for classifier requests.
    classifier_max_input_len: Maximum allowable input length for classifier prompts in tokens.
    banned_phrases: List of phrases to avoid in the chatbot's response.
    post_process_response: Whether to apply post-processing on chatbot responses to clean them.
    classifier_type: Type of classifier used for decision-making (e.g., "openai").
    classifier_path: Model path or API endpoint for the classifier.
    instruction_template: Template defining how the instruction and last user response are included in prompts.
    reply_start_type: Specifies how reply starts should be formatted. Options are "suffix", "prefix", or "none".
    default_reply_start_template: Template for reply starts, used to prepend or append text to replies.
    user_instruction_template: Template for user instructions when simulating user behavior.
    default_question_prompt: Default prompt used when asking multiple-choice or yes/no questions.
    default_transition_context: Number of conversational turns to include as context for transition questions.
    reply_suffix_inst_conversion: Template for modifying instructions in reply_suffix nodes.
"""

    




        if banned_phrases is None:
            banned_phrases=BANNED_PHRASES

        if error_response is None:
            error_response = ERROR_RESPONSE

        if chatbot_generation_args is None:
            chatbot_generation_args=CHATBOT_GENERATION_ARGS

        if instruction_template is None:
            instruction_template=INSTRUCTION_TEMPLATE



        if default_question_prompt is None:
            default_question_prompt = DEFAULT_QUESTION_PROMPT



        if default_reply_start_template is None:
            default_reply_start_template = DEFAULT_REPLY_START_TEMPLATE



   
        self.max_response_len=max_response_len

        self.default_prompt=default_prompt
        self.agent_name=agent_name
        self.user_name=user_name
        self.instruction_name=instruction_name
        self.chatbot_type=chatbot_type
        self.chatbot_path=chatbot_path
        self.system_prompt_in_turns=system_prompt_in_turns
        self.error_response=error_response
        self.chatbot_generation_args=chatbot_generation_args
        self.chatbot_max_tries=chatbot_max_tries
        self.chatbot_wait_per_try=chatbot_wait_per_try
        self.chatbot_max_input_len = chatbot_max_input_len
        self.classifier_max_tries=classifier_max_tries
        self.classifier_wait_per_try=classifier_wait_per_try
        self.classifier_max_input_len = classifier_max_input_len
        self.banned_phrases=banned_phrases
        self.post_process_response=post_process_response
        self.classifier_type=classifier_type
        self.classifier_path=classifier_path

        self.instruction_template=instruction_template

        if not reply_start_type in ALLOWED_REPLY_START_TYPES:
            raise Exception("Invalid reply start type " +reply_start_type)
        else:
            self.reply_start_type=reply_start_type

        self.default_reply_start_template=default_reply_start_template
        self.reply_start = self.default_reply_start_template.replace(AGENT_NAME_TOKEN,self.agent_name)

        self.user_instruction_template=user_instruction_template
        self.default_question_prompt=default_question_prompt
        self.default_transition_context = default_transition_context

        # if chat_exact_inst_conversion is None:
        #     chat_exact_inst_conversion=CHAT_EXACT_INST_CONVERSION

        # self.chat_exact_inst_conversion=chat_exact_inst_conversion

        # if thought_exact_inst_conversion is None:
        #     thought_exact_inst_conversion=THOUGHT_EXACT_INST_CONVERSION
        # self.thought_exact_inst_conversion=thought_exact_inst_conversion

        if reply_suffix_inst_conversion is None:
            reply_suffix_inst_conversion=REPLY_SUFFIX_INST_CONVERSION
        self.reply_suffix_inst_conversion=reply_suffix_inst_conversion










