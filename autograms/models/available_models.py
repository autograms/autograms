from .openai_chatbot import OpenAIChatbot
from .huggingface_chatbot import HuggingfaceChatbot
from .openai_classifier import OpenAIClassifier
from .huggingface_classifier import HuggingfaceClassifier



CHATBOT_TYPES={"openai":OpenAIChatbot,"huggingface":HuggingfaceChatbot}
CLASSIFIER_TYPES={"openai":OpenAIClassifier,"huggingface":HuggingfaceClassifier}




