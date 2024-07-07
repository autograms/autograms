
from autograms import Autogram, AutogramConfig


import json

API_KEY_FILE = "../../api_keys.json"
with open(API_KEY_FILE) as f:
      api_keys = json.load(f)

#arguments to autogram config allow default settings to be changed
config = AutogramConfig()

#initializes incomplete autogram that we will add nodes to
autogram = Autogram(autogram_config=config,api_keys=api_keys)

# uncomment to use local huggingface models
# api_keys ={}
# config = AutogramConfig(classifier_type="huggingface",chatbot_type="huggingface",\
#   chatbot_path="mistralai/Mistral-7B-Instruct-v0.1",classifier_path="mistralai/Mistral-7B-Instruct-v0.1")
# autogram = Autogram(api_keys = api_keys,autogram_config = config)

autogram.add_node(
      action = "chat_exact",
      name = "ask_question",
      transitions = ['tell_about_ai', 'ask_user_preference'],
      instruction = "Would you like me to tell you more about the latest advances in AI?",
      transition_question = "Does the user want to talk about ai?",
      transition_choices = ['yes', 'no'],
      )


autogram.add_node(
      action = "chat",
      name = "tell_about_ai",
      transitions = ['continue_conversation'],
      instruction = ("Tell the user about the latest advances in AI. Mention that"
        "a new framework called AutoGRAMS was recently released that allows greater control over AI agents."),
      )

autogram.add_node(
      action = "chat",
      name = "ask_user_preference",
      transitions = ['continue_conversation'],
      instruction = "Confirm with the user the user what they would prefer to talk about.",
      )


autogram.add_node(
      action = "chat",
      name = "continue_conversation",
      transitions = ['continue_conversation'],
      instruction = "Respond to the user.",
      )

autogram.update(finalize=True)
from autograms.graph_utils import visualize_autogram

visualize_autogram(autogram,root_path="simple_example")

memory_object=None
user_reply=""
while True:
      reply,memory_object = autogram.reply(user_reply,memory_object=memory_object)
      print("Agent: " + reply)
      user_reply = input("User: ")


