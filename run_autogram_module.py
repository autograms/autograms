import json
from autograms import Autogram, AutogramConfig


import pandas as pd
import argparse
import os
import importlib.util
import types
from collections import OrderedDict
from psyfy_pythonic import main as chatbot




def load_function_with_exec(file_path, function_name):
    """Dynamically load a function from a Python file using exec.

    Args:
        file_path (str): Path to the Python file.
        function_name (str): Name of the function to extract.

    Returns:
        function: The extracted function.
    """
    global_namespace = {}
    local_namespace = {}
    
    # Read the file content
    with open(file_path, "r") as file:
        code = file.read()
    
    # Execute the code in a clean namespace
    exec(code, global_namespace, local_namespace)
    
    # Extract the function
    func = global_namespace.get(function_name) or local_namespace.get(function_name)
    
    if not callable(func):
        raise ValueError(f"Function '{function_name}' not found in {file_path}.")
    
    return func



def load_module_from_file(file_path,module_name="module1"):
    
    spec = importlib.util.spec_from_file_location(module_name,file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


        

    return module



def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--autogram_file', type=str,help='.py file with autogram')
    parser.add_argument('--root_function', type=str,help='root function in autogram file')
    parser.add_argument('--api_key_file',type=str,help='api key file')
    parser.add_argument('--config_file',type=str,default=None,help='config file')

    args = parser.parse_args()


    
    autogram_file = args.autogram_file

    module=load_module_from_file(autogram_file)

    root_function =  getattr(module, args.root_function)

    import pdb;pdb.set_trace()

    if not args.api_key_file is None:
        fid = open(args.api_key_file)
        api_keys = json.load(fid)
        
    else:
        api_keys=dict()

    

    if args.config_file is None:


        autogram_config=AutogramConfig()
    else:


        initial_args = {}
        with open(args.config_file) as fid:
            config = json.load(fid)

        config={**initial_args, **config }

        autogram_config=AutogramConfig(**config)

    autogram= Autogram(autogram_config=autogram_config,root_function=root_function,api_keys=api_keys)




    chat_reply,memory_object = autogram.reply()

 
    while True:

        #shows how memory can be loaded and saved to continue old conversation
      #  memory_str = autogram.serialize(memory_object)
       # memory_object = autogram.deserialize(memory_str)

        print(chat_reply)
        
        user_reply = input("user reply: ")


        chat_reply,memory_object = autogram.reply(user_reply,memory_object=memory_object,test_mode=False)







if __name__ == '__main__':
    main()