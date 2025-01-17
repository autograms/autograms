api_keys={}


from . import openai_models
from ..memory import get_memory

def get_langchain_embeddings_settings():
    """
    Return a dictionary of settings compatible with LangChain's OpenAIEmbeddings (or similar).
    All backends are assumed to be routed through an OpenAI-compatible proxy for embeddings.
    """

    memory_object = get_memory()
    config = memory_object.config

    return {
        "model": config.embedding_path,                 # e.g. "text-embedding-ada-002", or local proxy label
        "openai_api_base": config.embedding_proxy_address, 
        # Again, pass "openai_api_key" if needed; skip otherwise
    }

def get_langchain_chat_settings():
    """
    Return a dict of settings for LangChain's ChatOpenAI (or any OpenAI-compatible chat model),
    including all fields from config.chatbot_generation_args except batch_size.
    """

    memory_object = get_memory()
    config = memory_object.config

    # Copy the generation args, removing 'batch_size' if present.
    gen_args = dict(config.chatbot_generation_args or {})

    # Build the default settings dictionary.
    settings = {
        "model_name": config.chatbot_path,                # e.g. "gpt-3.5-turbo"
        "openai_api_base": config.chatbot_proxy_address,  # e.g. "http://localhost:8080/v1"
        "max_tokens": config.max_tokens,            # map config.max_response_len
    }

    # Merge in the rest of the generation args (temperature, etc.).
    # Now, if 'temperature' or other fields exist in gen_args, they get added/overwritten here.
    settings.update(gen_args)

    return settings