
# AutogramConfig Documentation

`AutogramConfig` is the main configuration class in AutoGRAMS. It consolidates all the settings for **model and prompt settings** in AutoGRAMS. This reference explains every parameter, how the config interacts with other parts of AutoGRAMS, and how users can take advantage of it to customize their chatbot experience.

## Table of Contents

- [Overview](#overview)
- [Class Definition](#class-definition)
- [Parameters](#parameters)
- [Usage Patterns](#usage-patterns)
- [Overriding Config at Runtime](#overriding-config-at-runtime)
- [Examples](#examples)

---

## Overview

In AutoGRAMS:

- **Chatbot modules** and **functions** usually do not hardcode model details or generation arguments.
- An `AutogramConfig` object is passed when an `Autogram` is initialized. This dictates which model endpoints to call, max generation lengths, how many retries to attempt, how prompts are structured, etc.


- when using the `run_autogram.py` script to run your autogram, you can also pass in the config as a json file with the desired arguments, for example:
    - `run_autogram.py --autogram_file path/to/autogram/file.py --config_file path/to/config/file.json`


---

## Class Definition

```python
class AutogramConfig():
    def __init__(
        self,
        max_tokens=1024,
        default_prompt="You are an agent.",
        agent_name="Agent",
        user_name="User",
        instruction_name="Instruction",
        chatbot_type="openai",
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
        classifier_mode="json",
        embedding_type=None,
        embedding_path="text-embedding-3-small",
        instruction_template=None,
        reply_start_type="suffix",
        default_reply_start_template=None,
        user_instruction_template=None,
        default_question_prompt=None,
        default_transition_context=1,
        reply_suffix_inst_conversion=None,
        chatbot_proxy_port=8080,
        classifier_proxy_port=None,
        embedding_proxy_port=None,
        **kwargs
    ):
        ...
```

---

## Parameters

Below is a **comprehensive list** of the parameters that define an `AutogramConfig`. Some parameters have defaults and might not need explicit changes unless you want to customize certain behavior.

| Parameter                        | Type             | Default                        | Description                                                                                                                                                                                         |
|---------------------------------|------------------|--------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **max_tokens**                  | int             | `1024`                         | Maximum response length in tokens. Similar to OpenAI’s `max_tokens` or HuggingFace’s token limit.                                                                                                   |
| **default_prompt**              | str             | `"You are an agent."`          | Starting prompt for your chatbot or agent, used if no other system prompt is set.                                                                                                                   |
| **agent_name**                  | str             | `"Agent"`                      | Name of the AI assistant, used in prompts and for generating structured replies.                                                                                                                    |
| **user_name**                   | str             | `"User"`                       | Name of the user, used in conversation transcripts or for labeling user turns.                                                                                                                     |
| **instruction_name**            | str             | `"Instruction"`                | Label for the instruction token in your conversation templates. Typically appended to the system prompt.                                                                                           |
| **chatbot_type**                | str             | `"openai"`                     | Specifies which underlying model or approach is used for the chatbot. Options might include `"openai"`, `"proxy"`, or `"huggingface_tgi"`.                                                          |
| **chatbot_path**                | str             | `"gpt-4o"`                     | Model path or endpoint for the chatbot. For `"openai"`, this might be a model name (e.g., `"gpt-3.5-turbo"`). For `"proxy"`, an endpoint or model identifier.                                       |
| **system_prompt_in_turns**      | bool            | `False`                        | If `True`, the system prompt is embedded in the first user turn (for certain system behaviors). If `False`, it’s sent as a dedicated system message.                                               |
| **error_response**              | str             | `None` → fallback to internal  | The fallback response if the chatbot encounters an error. If `None`, uses a default message.                                                                                                        |
| **chatbot_generation_args**     | dict            | `{"temperature": 0.7}`         | A dictionary of generation parameters akin to OpenAI or HF model arguments. E.g., `{"temperature":0.8,"top_p":0.9}`.                                                                               |
| **chatbot_max_tries**           | int             | `3`                            | Maximum number of retries if the chatbot request fails.                                                                                                                                            |
| **chatbot_wait_per_try**        | int             | `5`                            | Number of seconds to wait between retries for chatbot requests.                                                                                                                                    |
| **chatbot_max_input_len**       | int             | `3500`                         | Maximum allowable input length in tokens for the chatbot prompt.                                                                                                                                    |
| **classifier_max_tries**        | int             | `2`                            | Maximum number of retries for classification requests (e.g., yes/no or multiple-choice logic).                                                                                                      |
| **classifier_wait_per_try**     | int             | `5`                            | Wait time between retries for classifier requests.                                                                                                                                                 |
| **classifier_max_input_len**    | int             | `2048`                         | Token limit for classifier prompts.                                                                                                                                                                |
| **exclude_classifier_system_prompt** | bool      | `False`                        | If `True`, the system prompt is not appended for classification. Useful if you want classifier logic to be minimal.                                                                                |
| **banned_phrases**              | list[str]       | `None` → fallback to a default | A list of phrases the chatbot should avoid. If the chatbot produces any of these, a retry or a filtered response may be triggered.                                                                  |
| **post_process_response**       | bool            | `True`                         | If `True`, the agent’s final response is post-processed (e.g., removing certain artifacts).                                                                                                        |
| **classifier_type**             | str             | `None` → fallback to `chatbot_type` | The model type for classifier logic. If `None`, defaults to `chatbot_type`. Examples: `"openai"`, `"huggingface_tgi"`, or `"proxy"`.                                                              |
| **classifier_path**             | str             | `None` → fallback to `chatbot_path` | The model path or endpoint for classifier. If `None`, defaults to `chatbot_path`.                                                                                                                  |
| **classifier_mode**             | str             | `"json"`                       | How classification is performed: `"logit"` or `"json"`. If `"logit"`, the model must support logit bias or special classification logic.                                                           |
| **embedding_type**              | str             | `None` → `"proxy"/"openai"` logic | Embedding model type, e.g., `"openai"`, `"proxy"`. If `None` and `chatbot_type == "proxy"`, we set `"proxy"`, else `"openai"`.                                                                    |
| **embedding_path**              | str             | `"text-embedding-3-small"`     | Model path/endpoint for the embedding model.                                                                                                                                                       |
| **instruction_template**        | str             | `None` → uses a default        | Template for how the instruction and user response are combined.                                                                                                                                  |
| **reply_start_type**            | str             | `"suffix"`                     | How to format reply starts in the conversation. Must be one of `"suffix"`, `"prefix"`, or `"none"`.                                                                                                |
| **default_reply_start_template** | str            | Various default                | The base template for reply starts.                                                                                                                                                                |
| **user_instruction_template**   | str             | `None`                         | Template for user instructions if you simulate user messages.                                                                                                                                      |
| **default_question_prompt**     | str             | `None` → fallback to default   | The default prompt text used for multiple-choice or yes/no questions.                                                                                                                              |
| **default_transition_context**  | int             | `1`                            | Number of conversation turns to include for context transitions.                                                                                                                                  |
| **reply_suffix_inst_conversion**| str             | `None` → fallback              | Template for instructing the chatbot how to handle `reply_suffix` nodes.                                                                                                                           |
| **chatbot_proxy_port**          | int             | `8080`                         | Port for chatbot proxies.                                                                                                                                                                         |
| **classifier_proxy_port**       | int             | `None` → fallback to `chatbot_proxy_port` | Port for classifier proxies if different from chatbot.                                                                                                      |
| **embedding_proxy_port**        | int             | `None` → fallback to `chatbot_proxy_port` | Port for embedding proxies if different.                                                                                                                    |
| **\*\*kwargs**                  | dict            | N/A                            | Additional arguments for **deprecated fields**. Raises error if not recognized.                                                                                                                    |

---



## Usage Patterns

1. **Creating a Default Config**  
   ```python
   config = AutogramConfig()
   # uses GPT-4o with temperature=0.7 (OpenAI style), 1024 max_tokens, etc.
   ```

2. **Customizing**  
    
   ```python
   config = AutogramConfig(
       chatbot_type="proxy",
       chatbot_path="http://localhost:8080/v1",
       max_tokens=1500,
       chatbot_generation_args={"temperature": 0.5},
   )
   ```


---

## Overriding Config at Runtime
  


- If do you want to override or hardcode certain behaviors (e.g., temperature, max_tokens, or a specific model path), you can do so in the config or by passing openai style arguments to model calling functions in `autograms.functional` 
    - for example
        ```python
        reply_instruction(instruction="reply to the user",max_tokens=2048).
        ```
    - if you want to reuse certain hardcoded behaviors that over ride the config, you could do something like
        ```python
        model1_settings= {"model":"gpt-3.5-turbo","max_tokens":2048}
        reply_instruction(instruction="reply to the user and ask a question",**model1_settings).
        reply_instruction(instruction="reply to the user with a follow up question",**model1_settings).
        ```
- overriding max_tokens or other generation args for certain responses can be useful for specific `thought()` or `reply_instruction()` calls. However, overwriting the "model" argument probably isn't necessary for most applications, unless you want to use completely different models for different calls. The config already lets you set different models for LLM-based classification, generation, and embeddings, so often its best practice to set the model names in the config so they can be more easily changed and the autogram module can be model agnostic.
