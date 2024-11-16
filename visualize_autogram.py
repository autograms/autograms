import json
from autograms.program_control import AutogramsFunction
from autograms.graph_utils import compile_graph

import pandas as pd
import argparse
import os
import importlib.util
import types
from collections import OrderedDict



# def import_module_by_file(file_path):


#     loader = importlib.machinery.SourceFileLoader("__temp__", file_path)
#     module = types.ModuleType(loader.name)
#     loader.exec_module(module)

#     return module.autogram






# def load_module_from_file(file_path,module_name="module1"):
    
#     spec = importlib.util.spec_from_file_location(module_name,file_path)
#     module = importlib.util.module_from_spec(spec)
#     spec.loader.exec_module(module)


        

#     return module



def main():
    # Set up argument parsing for command-line arguments
    parser = argparse.ArgumentParser()

    # Argument for specifying the folder to save graph files
    parser.add_argument('--save_folder', type=str, help='new folder for graph files',  required=True)
    
    # Argument for specifying the file format of the graph image (e.g., png, pdf)
    parser.add_argument('--graph_format', type=str, default="png", help='file format of graph image file (png, pdf, etc.)')
    
    # Argument for selecting the chatbot example module to graph
    parser.add_argument('--example_name', type=str,   required=True)
    args = parser.parse_args()

    # Dynamically load a chatbot example module based on the provided example_name
    if args.example_name == "simple_example":
        from examples import simple_example as module
    elif args.example_name == "fraction_tutor":
        from examples import fraction_tutor as module
    elif args.example_name == "general_tutor":
        from examples import general_tutor as module
    elif args.example_name == "recruiter":
        from examples import recruiter as module
    else:
        # Raise an error if no valid example is provided
        # Alternatively, replace this raise statement with a custom import statement to set module
        raise Exception("No example_name defined. If you wish to use your own example, delete this exception and replace it with an import statement for your example")

    # Create a dictionary to store functions that will be graphed
    functions_to_graph = OrderedDict()

    # Iterate through all attributes in the loaded module
    for submodule_name in dir(module):
        submodule = getattr(module, submodule_name)
        
        # Check if the attribute is an AutogramsFunction
        if isinstance(submodule, AutogramsFunction):
            functions_to_graph[submodule_name] = submodule

    # Generate and save visualizations for each Autograms function
    for name in functions_to_graph:
        # Uncomment the following lines to graph specific functions for debugging:
        # if not(name == "intro_start"):
        #     continue

        # Compile the graph for the function
        graph = compile_graph(functions_to_graph[name])
        
        # Save the graph visualization in the specified folder and format
        graph.save_visualization(args.save_folder)



    #import pdb;pdb.set_trace()







if __name__ == '__main__':
    main()