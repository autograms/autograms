

from autograms.finetuning.model_simulation import ChatbotSimulator
from autograms import AutogramConfig,Autogram, load_autogram,use_config, autograms_function
from autograms.functional import reply_instruction
import json
import os
import argparse

@autograms_function()
def default_user_chatbot():
    while True:
        reply_instruction("Reply as the user in the conversation.")

def main():
    # Set up argument parsing for command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--api_key_file', type=str, help='api key file')
    parser.add_argument('--config_file', type=str, default=None, help='config file')
    parser.add_argument('--user_config_file', type=str, default=None, help='user config file')
    parser.add_argument('--userbot_file', type=str, default=None)
    parser.add_argument('--memory_file', type=str, default=None, help='memory file to initialize from')
    parser.add_argument('--user_memory_file', type=str, default=None, help='user memory file to initialize from')
    parser.add_argument('--predefined_userbot', type=str, default="variable")
    parser.add_argument('--autogram_file', type=str, required=True,help="Load autogram from .py module file.")
    parser.add_argument('--save_dir', type=str,default = "simulation_data")
    parser.add_argument('--simulation_list_file', type=str,default=None)
    parser.add_argument('--num_turns', type=int,default = 1)
    parser.add_argument('--num_examples', type=int,default = 5)
    parser.add_argument('--allow_overwrite', action="store_true")

    args = parser.parse_args()

    if not os.path.exists(args.save_dir):
        os.makedirs(args.save_dir)
    else:
        if not args.allow_overwrite:
            raise Exception(f"Directory {args.save_dir} already exist. Use a different --save_dir argument or use --allow_overwrite to override this error and write to this directory anyway")


    # Load API keys from a file if provided, otherwise use an empty dictionary
    if not args.api_key_file is None:
        fid = open(args.api_key_file)
        api_keys = json.load(fid)
    else:
        api_keys = None


    # Load or initialize configuration
    if args.config_file is None:

        autogram_config = AutogramConfig(chatbot_path = 'gpt-4o')
    else:
        initial_args = {}
        with open(args.config_file) as fid:
            config = json.load(fid)
        # Merge default and loaded config
        config = {**initial_args, **config}
        autogram_config = AutogramConfig(**config)

    # Load or initialize configuration
    if args.user_config_file is None:

        autogram_config = AutogramConfig(chatbot_path = 'gpt-4o-mini')
    else:
        initial_args = {}
        with open(args.user_config_file) as fid:
            config = json.load(fid)
        # Merge default and loaded config
        config = {**initial_args, **config}

        user_config = AutogramConfig(**config)
    user_config  = AutogramConfig(chatbot_path = "gpt-4o-mini")

    chatbot,init_chatbot = load_autogram(args.autogram_file)
    autogram = Autogram(autogram_config=autogram_config, root_function=chatbot, api_keys=api_keys,supervisor_mode=True)

    

    if chatbot is None:
        raise Exception(f"Must have chatbot() function in module defined in file {args.autogram_file}")

    if not init_chatbot is None:
        with use_config(autogram_config):
            init_chatbot()


    if not args.userbot_file is None:
        user_chatbot,user_init_chatbot = load_autogram(args.userbot_file)
        if not user_init_chatbot is None:
            with use_config(user_config):
                user_init_chatbot()

    else:
        user_chatbot = default_user_chatbot
      
    user_autogram = Autogram(autogram_config=user_config, root_function=user_chatbot, api_keys=api_keys,supervisor_mode=True)


    if not args.memory_file is None:
        with open(args.memory_file) as fid:
            raw_memory = fid.read()
        
    else:
        raw_memory = None

    if not args.user_memory_file is None:
        with open(args.user_memory_file) as fid:
            raw_user_memory = fid.read()
      
    else:
        raw_user_memory = None


    if not(args.simulation_list_file is None):
        with open(args.user_memory_file) as fid:
            simulation_list = json.load(fid)
        if len(simulation_list)>args.num_examples:
            print(f"Since simulation_list_file is provided, we will simulate all {len(simulation_list)} scenarios in the file and ignore num_examples which was set to {args.num_examples}")

    else:
        simulation_list = [{"num_turns":args.num_turns,"chatbot_kwargs":{},"user_kwargs":{}}]*args.num_examples

    simulator = ChatbotSimulator(autogram,user_autogram)
    
    for i in range(len(simulation_list)):
        simulation = simulation_list[i]
        if not "num_turns" in simulation:
            simulation["num_turns"]=args.num_turns

        print(f"Simulating example {i}")
        if not(raw_memory is None):
            chatbot_memory_init = autogram.deserialize(raw_memory)
        else:
            chatbot_memory_init = None

        if not(raw_user_memory is None):
            user_memory_init = user_autogram.deserialize(raw_memory)
        else:
            user_memory_init = None
        
        new_memory,new_user_memory = simulator.simulate(**simulation,user_memory = user_memory_init,chatbot_memory=chatbot_memory_init)
        new_memory_raw = autogram.serialize(new_memory)

        save_path = os.path.join(args.save_dir,f"example{i}.pkl")
       
        with open(save_path,'w') as fid:
            fid.write(new_memory_raw)


        print(f"Saved example {i} in {save_path}")


if __name__=="__main__":
    main()







