from autograms.graph_utils import visualize_autogram
from autograms import read_autogram
import json

API_KEY_FILE = "../../api_keys.json"
with open(API_KEY_FILE) as f:
      api_keys = json.load(f)


autogram = read_autogram("simple_example_compiled.py",api_keys=api_keys)

visualize_autogram(autogram,root_path="simple_example_compiled")

memory_object=None
user_reply=""
while True:
      reply,memory_object = autogram.reply(user_reply,memory_object=memory_object)
      print("Agent: " + reply)
      user_reply = input("User: ")