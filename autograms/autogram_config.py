



import warnings

LAST_RESPONSE_TOKEN="<last_response>"
INSTRUCTION_TOKEN="<instruction>"
AGENT_NAME_TOKEN="<agent_name>"


BANNED_PHRASES=["that request","language model","provide a response","I can't respond","I cannot engage","I can't engage","I'm sorry, I can't","I'm sorry, I cannot","I cannot respond","I can't provide","I cannot provide","I can't fullful","I cannot fullfill","that prompt","that instruction","open ai"]
CHATBOT_GENERATION_ARGS={"temperature":0.7}
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

DEPRECATED_KWARGS = {
    "max_response_len": "max_tokens",  # Maps legacy `max_response_len` to openai compatible `max_tokens`.
}

class AutogramConfig():
    """
    Configuration object for AutoGRAMS.

    This class provides configuration options for managing various aspects of AutoGRAMS,
    including model settings, prompt generation, retries, and template definitions.

    Parameters:
        max_tokens (int): Maximum response length from the model in tokens (default: 1024).
        default_prompt (str): Starting prompt for the agent.
        agent_name (str): Name of the agent, used in prompt templates.
        user_name (str): Name of the user, used in prompt templates.
        instruction_name (str): Label for the instruction token in prompts.
        chatbot_type (str): Type of chatbot (e.g., "openai", "proxy", "huggingface_tgi").
        chatbot_path (str): Model path or API endpoint for the chatbot.
        system_prompt_in_turns (bool): Whether to include the system prompt in the first user turn (True) or as a normal system message (False).
        error_response (str): Fallback response when the chatbot encounters an error.
        chatbot_generation_args (dict): Arguments for chatbot generation (e.g., temperature, top_p).
        chatbot_max_tries (int): Maximum number of retries for chatbot requests.
        chatbot_wait_per_try (int): Number of seconds to wait between retries for chatbot requests.
        chatbot_max_input_len (int): Maximum allowable input length for chatbot prompts in tokens.
        classifier_max_tries (int): Maximum number of retries for classifier requests.
        classifier_wait_per_try (int): Number of seconds to wait between retries for classifier requests.
        classifier_max_input_len (int): Maximum allowable input length for classifier prompts in tokens.
        exclude_classifier_system_prompt (bool): Whether to exclude the system prompt for classifiers.
        banned_phrases (list[str]): List of phrases to avoid in chatbot responses.
        post_process_response (bool): Whether to post-process chatbot responses to clean them.
        classifier_type (str): Type of classifier (e.g., "openai", "proxy" or "huggingface_tgi").
        classifier_path (str): Model path or API endpoint for the classifier.
        classifier_mode (str): Mode of classification ("logit" or "json").
        embedding_type (str): Type of embedding model (e.g., "openai", "proxy").
        embedding_path (str): Model path or API endpoint for embeddings.
        instruction_template (str): Template defining the instruction and user response in prompts.
        reply_start_type (str): Formatting for reply starts ("suffix", "prefix", or "none").
        default_reply_start_template (str): Template for reply starts.
        user_instruction_template (str): Template for user instructions when simulating behavior.
        default_question_prompt (str): Default prompt for multiple-choice or yes/no questions.
        default_transition_context (int): Number of conversational turns to include for context.
        reply_suffix_inst_conversion (str): Template for modifying instructions in reply_suffix nodes.
        chatbot_proxy_port (int): Port for chatbot proxies (default: 8080).
        classifier_proxy_port (int): Port for classifier proxies (default: None, falls back to chatbot_proxy_port).
        embedding_proxy_port (int): Port for embedding proxies (default: None, falls back to chatbot_proxy_port).
        **kwargs: Additional arguments for handling deprecated fields.
    """
    def __init__(
            self,
            max_tokens=1024,
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
            exclude_classifier_system_prompt=False,
            banned_phrases=None,
            post_process_response=True,
            classifier_type=None,
            classifier_path=None,
            classifier_mode='json',
            embedding_type=None,
            embedding_path="text-embedding-3-small",
            instruction_template=None,
            reply_start_type="suffix",
            default_reply_start_template=None,
            user_instruction_template=None,
            default_question_prompt=None,
            default_transition_context=1,
            reply_suffix_inst_conversion=None,
            chatbot_proxy_port = 8080,
            classifier_proxy_port=None,
            embedding_proxy_port=None,
            **kwargs

        ):

    
        # Validate **kwargs
        unrecognized_kwargs = set(kwargs.keys()) - set(DEPRECATED_KWARGS.keys())
        if unrecognized_kwargs:
            raise ValueError(
                f"Unrecognized arguments: {', '.join(unrecognized_kwargs)}. "
            )




        if banned_phrases is None:
            banned_phrases=[]
            
        elif banned_phrases=="default":
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




        self.max_tokens=max_tokens

        self.default_prompt=default_prompt
        self.agent_name=agent_name
        self.user_name=user_name
        self.instruction_name=instruction_name
        self.chatbot_type=chatbot_type
        self.chatbot_path=chatbot_path
        self.system_prompt_in_turns=system_prompt_in_turns
        self.error_response=error_response
        if 'batch_size' in chatbot_generation_args:
            print("WARNING: batch_size no longer supported for config generation args, deleting batch_size")
            del chatbot_generation_args['batch_size']
        self.chatbot_generation_args=chatbot_generation_args
        self.chatbot_max_tries=chatbot_max_tries
        self.chatbot_wait_per_try=chatbot_wait_per_try
        self.chatbot_max_input_len = chatbot_max_input_len
        self.classifier_max_tries=classifier_max_tries
        self.classifier_wait_per_try=classifier_wait_per_try
        self.classifier_max_input_len = classifier_max_input_len
        self.banned_phrases=banned_phrases
        self.post_process_response=post_process_response
   

        if classifier_type is None:
            classifier_type=chatbot_type
       
        self.classifier_type=classifier_type

        if classifier_path is None:
            classifier_path=chatbot_path

        if not classifier_mode in ["logit","json"]:
            raise Exception("classifier_mode is not valid, must be either `logit` or `json`") 

        if classifier_mode == "logit" and self.classifier_type=="huggingface":
            print(f"WARNING: classifier_mode: {classifier_mode} and classifier type {self.classifier_type} are likely incompatible due to Huggingface TGI not fully supporting logit_bias argument, although this could change in the future if Huggingface pushes an update. As of 1-14-2025, this combination will result in errors. It is strongly recommended to restart and use classifier_type='json' instead.")
        elif classifier_mode == "logit" and not self.classifier_type[:3]=="gpt":
            print(f"WARNING: unable to verify if classifier_mode: {classifier_mode} and classifier type: {self.classifier_type} are compatible. This may result in downstream errors. classifier_type='json' is supported by more models.")

        self.classifier_mode = classifier_mode

        self.classifier_path=classifier_path
        if embedding_type is None:
            if chatbot_type=="proxy":
                embedding_type="proxy"
            else:
                embedding_type="openai"


        self.embedding_type=embedding_type

        self.embedding_path = embedding_path



        self.exclude_classifier_system_prompt=exclude_classifier_system_prompt

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


        if reply_suffix_inst_conversion is None:
            reply_suffix_inst_conversion=REPLY_SUFFIX_INST_CONVERSION
        self.reply_suffix_inst_conversion=reply_suffix_inst_conversion

        self.proxy_address =f"http://localhost:{chatbot_proxy_port}/v1"
        if classifier_proxy_port is None:
             classifier_proxy_port = chatbot_proxy_port

        self.classifier_proxy_address =f"http://localhost:{classifier_proxy_port}/v1"

  

        if embedding_proxy_port is None:

                        
            if chatbot_type=="huggingface_tgi" and not embedding_type=="openai":
                raise Exception("you must specify separate embedding_proxy_port for embeddings or use openai. If you do not use embeddings, you can switch to embedding_type = 'openai' even if you have no api key, or pass an unused port for embedding_proxy_port without causing errors.")
            
            embedding_proxy_port = chatbot_proxy_port

        self.embedding_proxy_address =f"http://localhost:{embedding_proxy_port}/v1"



        # Handle deprecated arguments
        for legacy_key, new_key in DEPRECATED_KWARGS.items():
            if legacy_key in kwargs:
                warnings.warn(
                    f"'{legacy_key}' is deprecated and may be removed in future versions. "
                    f"Use '{new_key}' instead.",
                    DeprecationWarning,
                )
                setattr(self, new_key, kwargs[legacy_key])







