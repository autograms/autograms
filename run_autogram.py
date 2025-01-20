import json
from autograms import Autogram, AutogramConfig, use_config, load_autogram


import pandas as pd
import argparse
import os






def main():
    # Set up argument parsing for command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--api_key_file', type=str, help='api key file')
    parser.add_argument('--config_file', type=str, default=None, help='config file')
    parser.add_argument('--saveload_file', type=str, default=None, help='file to reload memory from file')
    parser.add_argument('--example_name', type=str, default="autograms_seed_agent")
    parser.add_argument('--autogram_file', type=str, default=None,help="Load autogram from .py module file instead of importing directly in code. useful for custom examples")
    parser.add_argument('--model_name', type=str, default="gpt-4o")
    parser.add_argument('--model_type', type=str, default="openai")
    parser.add_argument('--embedding_model_name', type=str, default="text-embedding-3-small")
    parser.add_argument('--embedding_model_type', type=str, default=None)
    parser.add_argument('--proxy_port', type=str, default=8080)
    parser.add_argument('--embedding_proxy_port', type=str, default=None)

    args = parser.parse_args()

    # Load API keys from a file if provided, otherwise use an empty dictionary
    if not args.api_key_file is None:
        fid = open(args.api_key_file)
        api_keys = json.load(fid)
    else:
        api_keys = None


    # Load or initialize configuration
    if args.config_file is None:
        if args.example_name == "autograms_seed_agent":
            chatbot_generation_args={"temperature":0.4}
            autogram_config = AutogramConfig(chatbot_path = args.model_name,chatbot_max_input_len=40000,classifier_max_input_len=40000,classifier_path = args.model_name,max_response_len=4096,chatbot_generation_args=chatbot_generation_args,exclude_classifier_system_prompt=True,chatbot_type = args.model_type,chatbot_proxy_port=args.proxy_port,embedding_proxy_port = args.embedding_proxy_port,embedding_type=args.embedding_model_type,embedding_path=args.embedding_model_name,reply_start_type='none')
        else:
            autogram_config = AutogramConfig(chatbot_path = args.model_name,classifier_path = args.model_name,chatbot_type = args.model_type,chatbot_proxy_port=args.proxy_port,embedding_proxy_port = args.embedding_proxy_port,embedding_type=args.embedding_model_type,embedding_path=args.embedding_model_name,reply_start_type='none')
    else:
        initial_args = {}
        with open(args.config_file) as fid:
            config = json.load(fid)
        # Merge default and loaded config
        config = {**initial_args, **config}
        autogram_config = AutogramConfig(**config)

    if args.autogram_file is None:

        # Load chatbot example based on the provided example_name
        if args.example_name == "autograms_seed_agent":
            from examples.autograms_seed_agent import chatbot
        elif args.example_name == "doc_search":
            from examples.autograms_doc_search import chatbot, init_chatbot
            with use_config(autogram_config):
                init_chatbot()
        elif args.example_name == "simple_example":
            from examples.simple_example import chatbot
        elif args.example_name == "fraction_tutor":
            from examples.fraction_tutor import chatbot
        elif args.example_name == "general_tutor":
            from examples.general_tutor import chatbot
        elif args.example_name == "recruiter":
            from examples.recruiter import chatbot
        else:
            # Raise an error if no valid example is provided
            # can alternatively replace this raise statement with your own import statement to set chatbot function
            raise Exception("No example_name defined. If you wish to use your own example, delete this exception and replace it with an import statement for your example")

    else:
        chatbot,init_chatbot = load_autogram(args.autogram_file)

        if chatbot is None:
            raise Exception(f"Must have chatbot() function in module defined in file {args.autogram_file}")

        if not init_chatbot is None:
            with use_config(autogram_config):
                init_chatbot()

    autogram = Autogram(autogram_config=autogram_config, root_function=chatbot, api_keys=api_keys)


    # If a save/load file is provided and exists, load memory from it
    if not (args.saveload_file is None) and os.path.exists(args.saveload_file):
        with open(args.saveload_file) as fid:
            memory = fid.read()
        memory_object = autogram.deserialize(memory)
        
        # Resume from the last user reply saved in memory
        user_reply = memory_object.memory_dict['user_reply_to_save']
        chat_reply, memory_object = autogram.reply(user_reply, memory_object=memory_object)
    else:
        # Start a new conversation if no memory file is provided
        chat_reply, memory_object = autogram.reply()

    # Main loop for handling chat interaction
    while True:
        # Display the agent's reply along with the line number it came from
        print(f"reply from line number: {memory_object.memory_dict['stack'][-1]['line_number']}: {chat_reply}")

        # Prompt user for their reply
        user_reply = input("user reply: ")

        if user_reply=="exit":
            break
        if user_reply=="debug":
            #print(memory_object.memory_dict['model_turns'])
            print(f"Local variables in autogram:\n{memory_object.memory_dict['stack'][-1]['locals']}")
            import pdb;pdb.set_trace()
        
            user_reply = input("user reply: ")

        # Save the user's reply to memory for later reloads if a save/load file is provided
        if not args.saveload_file is None:
            memory_object.memory_dict['user_reply_to_save'] = user_reply


        # Serialize memory before the next reply to preserve the state
        memory_str_orig = autogram.serialize(memory_object)



        # Generate the next reply based on user input
        chat_reply, memory_object = autogram.reply(user_reply, memory_object=memory_object)

        # Save the updated memory to file if a save/load file is provided
        if not args.saveload_file is None:
            with open(args.saveload_file, 'w') as fid:
                fid.write(memory_str_orig)



if __name__ == '__main__':
    main()