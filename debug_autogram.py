import json
from autograms import Autogram, AutogramConfig, use_config, load_autogram


import pandas as pd
import argparse
import os






def main():
    # Set up argument parsing for command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, default=None, help='config file')
    parser.add_argument('--example_name', type=str, default="autograms_seed_agent")
    parser.add_argument('--autogram_file', type=str, default=None,help="Load autogram from .py module file instead of importing directly in code. useful for custom examples")
    parser.add_argument('--num_simulations',type=int,default=20)
    parser.add_argument('--turns_per_simulation',type=int,default=10)

    args = parser.parse_args()


    api_keys = None


    # Load or initialize configuration
    if args.config_file is None:
        autogram_config = AutogramConfig()
   
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

    autogram = Autogram(autogram_config=autogram_config, root_function=chatbot, api_keys=api_keys,test_mode=True)


    for i in range(args.num_simulations):
        chat_reply, memory_object = autogram.reply()
    
        # Main loop for handling chat interaction
        for j in range(args.turns_per_simulation):
            # Display the agent's reply along with the line number it came from
            print(f"reply from line number: {memory_object.memory_dict['stack'][-1]['line_number']}: {chat_reply}")

            # Prompt user for their reply
            user_reply = "<test user reply>"



            # Serialize memory before the next reply to preserve the state
            memory_str_orig = autogram.serialize(memory_object)

            memory_object= autogram.deserialize(memory_str_orig)



            # Generate the next reply based on user input
            chat_reply, memory_object = autogram.reply(user_reply, memory_object=memory_object)

    print(f"successfully simulated {args.num_simulations} users without errors")




if __name__ == '__main__':
    main()