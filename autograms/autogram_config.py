




LAST_RESPONSE_TOKEN="<last_response>"
INSTRUCTION_TOKEN="<instruction>"
AGENT_NAME_TOKEN="<agent_name>"


BANNED_PHRASES=["that request","language model","provide a response","I can't respond","I cannot engage","I can't engage","I'm sorry, I can't","I'm sorry, I cannot","I cannot respond","I can't provide","I cannot provide","I can't fullful","I cannot fullfill","that prompt","that instruction","open ai"]
CHATBOT_GENERATION_ARGS={"temperature":0.7,"batch_size":1}
ERROR_RESPONSE="Sorry, the system is down right now. Hopefully the system will be back soon and you can continue your conversation."
INSTRUCTION_TEMPLATE=LAST_RESPONSE_TOKEN+"\n\nInstruction for "+AGENT_NAME_TOKEN+ ": " +INSTRUCTION_TOKEN
DEFAULT_QUESTION_PROMPT="I need you to solve a multiple choice question.\n"

USER_INSTRUCTION_TEMPLATE=LAST_RESPONSE_TOKEN+"\n\nInstruction for user: "+INSTRUCTION_TOKEN
DEFAULT_REPLY_START_TEMPLATE=AGENT_NAME_TOKEN+ "'s reply:"



INTERJECTION_QUESTION="Which of the following is True?"

INTERJECTION_DEFAULT_ANSWER="None of the above."

PYTHON_BUILT_INS=["int","float","complex","list","tuple","range","dict","bytes", "bytearray","set","frozenset","str","sum","pow","abs","max","min","len","ord","chr","reversed","map","zip","type","print"]
PYTHON_IMPORTS=["import math","import operator","import functools","import ast"]

ALLOWED_REPLY_START_TYPES=["suffix","prefix","none"]


CHAT_EXACT_INST_CONVERSION="Reply to the user with the following text: "+INSTRUCTION_TOKEN 
THOUGHT_EXACT_INST_CONVERSION="Reply with this exact text: " +INSTRUCTION_TOKEN 
CHAT_SUFFIX_INST_CONVERSION="Respond to the user's last reply, and then include the **bold** text at the end of your response to direct the conversation:**" + INSTRUCTION_TOKEN  +"**. It is also okay for the whole response to be the bold text if it fits the situation."


    
class AutogramConfig():
    def __init__(
            self,
            max_response_len=256,
            default_prompt="You are an agent.",
            default_user_prompt="You are a user.",
            agent_name="Agent",
            user_name="User",
            instruction_name="Instruction",
            chatbot_type = "openai",
            chatbot_path="gpt-3.5-turbo-1106",
            error_response=None,
            chatbot_generation_args=None, 
            chatbot_max_tries=3,
            chatbot_wait_per_try=5,
            chatbot_max_input_len=4096,
            classifier_max_tries=2,
            classifier_wait_per_try=5,
            classifier_max_input_len=2048,
            banned_phrases=None,
            post_process_response=True,
            classifier_type="openai",
            classifier_path="gpt-3.5-turbo-1106",
            log_model_turns=True,
            start_state="start1",
            end_signal="<end>",
            instruction_template=None,
            reply_start_type="suffix",
            default_reply_start_template=None,
            user_instruction_template=None,
            default_question_prompt=None,
            default_transition_context=1,
            interjection_question=None,
            interjection_default_answer=None,
            default_probability_interjection=0.01,
            default_primary_prob_detla=0.3,
            chat_exact_inst_conversion=None,
            thought_exact_inst_conversion=None,
            chat_suffix_inst_conversion=None,
            python_built_ins=None,
            python_imports=None,
            self_referential=False,
            reference_memory_object=False,
            include_default_python_modules=False,
            python_modules={}
        ):
        """
        Initialize AutogramConfig
        Can be used to change the default agent settings if called with arguments and passed when initializing agent.

        

        args:
            max_response_len -- max response length from the model.
            default_prompt -- start prompt for agent. Can be changed on-the-fly with set_prompt and append_prompt actions from spreadsheet
            default_user_prompt -- start prompt for user. Can be changed on-the-fly with set_prompt and append_prompt actions from spreadsheet
            agent_name -- name of agent to used in prompts to model
            user_name -- name of user to be used in prompts to model
            instruction_name -- name of instruction to be used in prompts to model
            chatbot_type -- type of chatbot
            chatbot_path -- path (or api name) of chatbot
            error_response -- response if chatbot has error
            chatbot_generation_args -- generation args sent to chatbot
            chatbot_max_tries -- max tries for chatbot
            chatbot_wait_per_try -- number of seconds to wait between tries for chatbot
            chatbot_max_input_len -- truncate input if it's longer than this number of tokens
            classifier_max_tries -- max tries for classifier
            classifier_wait_per_try -- number of seconds to wait between tries for classifier
            classifier_max_input_len -- truncate input if it's longer than this number of tokens
            banned_phrases -- phrases we try to strongly discourage chatbot from generating, usually corresponding to refusal to follow instruction.
            post_process_response -- apply post processing to respond
            classifier_type -- type of classifier. Not that classifier is just a language model with restricted logits.
            classifier_path -- path (or api name of classifier) 
            log_model_turns -- log model turns in MemoryObject
            start_state -- default start state
            end_signal -- text signaling finish during user simulation
            instruction_template -- template for where to put instruction and last user reply in prompt
            reply_start_type -- reply start type. Can be 'suffix', 'prefix', or 'none'. 'prefix' is only possible for local and completion models.
            default_reply_start_template -- template for how reply start should look.
            user_instruction_template -- template for where to put instruction and last agent reply when passing prompt to simulate user
            default_question_prompt -- prompt for asking transition questions
            default_transition_context -- number of turns of context for predicting transitions
            interjection_question -- question to ask for predicting interjections
            interjection_default_answer -- default answer that leads to no interjection, usually meaning that none of the interjection conditions are true
            default_probability_interjection -- probability of simulating each interjection state
            default_primary_prob_detla -- how much more likely should first (default) transition be than all other transitions, which are uniform
            chat_exact_inst_conversion -- template for how modify instructions of chat_exact nodes
            thought_exact_inst_conversion=-- template for how modify instructions of thought_exact nodes
            chat_suffix_inst_conversion  -- template for how modify instructions of chat_suffix nodes
            python_built_ins -- allowable python built ins, any built in not listed is disabled
            python_imports -- python import statements to be applied to autogram
            self_referential -- allow the autogram to access and modify its own code via python nodes by passing a reference to itself using the variable name 'self'
            reference_memory_object -- allows the autogram to access its own memory object from python nodes using the variable '_memory_object'
            include_default_python_modules -- autromatically include all autograms python modules
            python_modules -- dictionary mapping names to python functions that will be addressable from within autogram
        
        
        """

        if banned_phrases is None:
            banned_phrases=BANNED_PHRASES

        if error_response is None:
            error_response = ERROR_RESPONSE

        if chatbot_generation_args is None:
            chatbot_generation_args=CHATBOT_GENERATION_ARGS

        if instruction_template is None:
            instruction_template=INSTRUCTION_TEMPLATE

        if user_instruction_template is None:
            user_instruction_template=USER_INSTRUCTION_TEMPLATE

        if default_question_prompt is None:
            default_question_prompt = DEFAULT_QUESTION_PROMPT

        if interjection_question is None:
            interjection_question=INTERJECTION_QUESTION
        if interjection_default_answer is None:
            interjection_default_answer=INTERJECTION_DEFAULT_ANSWER

        if default_reply_start_template is None:
            default_reply_start_template = DEFAULT_REPLY_START_TEMPLATE

        if python_built_ins is None:
            python_built_ins =  PYTHON_BUILT_INS
        if python_imports is None:
            python_imports = PYTHON_IMPORTS
        


    
        
        
   
        self.max_response_len=max_response_len
        self.default_user_prompt=default_user_prompt
        self.default_prompt=default_prompt
        self.agent_name=agent_name
        self.user_name=user_name
        self.instruction_name=instruction_name
        self.chatbot_type=chatbot_type
        self.chatbot_path=chatbot_path
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
        self.log_model_turns=log_model_turns
        self.start_state=start_state
        self.end_signal=end_signal
        self.instruction_template=instruction_template

        if not reply_start_type in ALLOWED_REPLY_START_TYPES:
            raise Exception("Invalid reply start type " +reply_start_type)
        else:
            self.reply_start_type=reply_start_type

        self.default_reply_start_template=default_reply_start_template

        self.user_instruction_template=user_instruction_template
        self.default_question_prompt=default_question_prompt
        self.default_transition_context = default_transition_context
        self.interjection_question =interjection_question
        self.interjection_default_answer =interjection_default_answer
        self.default_probability_interjection=default_probability_interjection
        self.default_primary_prob_detla=default_primary_prob_detla
        if chat_exact_inst_conversion is None:
            chat_exact_inst_conversion=CHAT_EXACT_INST_CONVERSION

        self.chat_exact_inst_conversion=chat_exact_inst_conversion

        if thought_exact_inst_conversion is None:
            thought_exact_inst_conversion=THOUGHT_EXACT_INST_CONVERSION
        self.thought_exact_inst_conversion=thought_exact_inst_conversion

        if chat_suffix_inst_conversion is None:
            chat_suffix_inst_conversion=CHAT_SUFFIX_INST_CONVERSION
        self.chat_suffix_inst_conversion=chat_suffix_inst_conversion

        self.python_built_ins  = python_built_ins 
        self.python_imports = python_imports
        
        self.self_referential=self_referential
        self.reference_memory_object=reference_memory_object


        self.python_modules = python_modules

        if include_default_python_modules:
            from . import python_modules 
        
            autogram_python_modules=python_modules.submodules
            self.python_modules =  {**self.python_modules, **autogram_python_modules}








