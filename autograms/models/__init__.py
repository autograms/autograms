from .chatbot import Chatbot
from .classifier import Classifier


from .openai_chatbot import OpenAIChatbot
from .openai_classifier import OpenAIClassifier

try:
    from .huggingface_chatbot import HuggingfaceChatbot
    from .huggingface_classifier import HuggingfaceClassifier



    CHATBOT_TYPES={"openai":OpenAIChatbot,"huggingface":HuggingfaceChatbot}
    CLASSIFIER_TYPES={"openai":OpenAIClassifier,"huggingface":HuggingfaceClassifier}

except:
    print("Warning, install pytorch to use models from huggingface transformers")

    CHATBOT_TYPES={"openai":OpenAIChatbot}
    CLASSIFIER_TYPES={"openai":OpenAIClassifier}
