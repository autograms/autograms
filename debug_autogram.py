import json
from autograms import Autogram, AutogramConfig


import pandas as pd
import argparse
import os






def main():
    # Set up argument parsing for command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, default=None, help='config file')
    parser.add_argument('--example_name', type=str, default="autograms_seed_agent")
    parser.add_argument('--num_simulations',type=int,default=20)
    parser.add_argument('--turns_per_simulation',type=int,default=10)

    args = parser.parse_args()


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



    api_keys = None

    # Load or initialize configuration
    if args.config_file is None:
        if args.example_name == "autograms_seed_agent":
            autogram_config = AutogramConfig(chatbot_max_input_len=40000,classifier_max_input_len=40000,max_response_len=4096,exclude_classifier_system_prompt=True)
        else:
            autogram_config = AutogramConfig()
    else:
        initial_args = {}
        with open(args.config_file) as fid:
            config = json.load(fid)
        # Merge default and loaded config
        config = {**initial_args, **config}
        autogram_config = AutogramConfig(**config)

    # Initialize the Autogram instance
    autogram = Autogram(autogram_config=autogram_config, root_function=chatbot, test_mode=True)

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