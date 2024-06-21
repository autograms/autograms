import json
from autograms import Autogram,AutogramCompiler,AutogramConfig
from autograms.graph_utils import HTML_TEMPLATE
import pandas as pd
import argparse
import os
import importlib.util
import types


def import_module_by_file(file_path):


    loader = importlib.machinery.SourceFileLoader("__temp__", file_path)
    module = types.ModuleType(loader.name)
    loader.exec_module(module)

    return module.autogram






def get_node_data(autogram,autogram_csv_dict,graph_node_names):

    node_data=dict()


    node_arg_dict=dict()



    for node_name in graph_node_names:
        node_string = "Node information for "+node_name

        if node_name in autogram.nodes.keys():
            node_obj = autogram.nodes[node_name]
            node_string+="\n\nAction: "+node_obj.action
            node_string+="\n\nInstruction: "+node_obj.instruction
            
            if not(node_obj.transition_question is None) and len(node_obj.transition_question)>0 and len(node_obj.transition_answers)>0:

                node_string+="\n\nTransition Question: "+node_obj.transition_question
                ABCDE="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                for i in range(len(node_obj.transition_answers)):
                    answer = node_obj.transition_answers[i]
                    letter=ABCDE[i]
                    node_string+="\n" +letter+ " (" +node_obj.transitions[i] + ")" +" -- " + answer

        if node_name in autogram_csv_dict.keys():
            for field in autogram_csv_dict[node_name].keys():
                if not field in ["action","transitons","name","instruction","transition_question"]:
                    if not "transition_choice" in field:
                        node_string+="\n\n" + field + ": "+ str(autogram_csv_dict[node_name][field])


        node_data[node_name]=node_string
                   

    return node_data




def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--autogram_file', type=str,help='.py or .csv file with autogram, will support other spreadsheet formats later')
    parser.add_argument('--filter_category', type=str,default=None,help='only draw graph for states of specific category')
    parser.add_argument('--label_by_inst', action="store_true",help='label graph by instruction instead of node name')
    parser.add_argument('--read_as_pure_python', action="store_true",help="load autogram as pure python instead of compiled from python")
    parser.add_argument('--graph_format',type=str,default="png",help='file format of graph image file (png, pdf, etc.)')
    args = parser.parse_args()



    
    autogram_file = args.autogram_file
    ind = autogram_file.rfind(".")
    if ind<0:
        raise Exception("invalid autogram file")
    path_and_name = autogram_file[:ind]
    ext=autogram_file[ind:]


    if ext==".py":
        fid = open(args.autogram_file)
        code=fid.read()

        if args.read_as_pure_python:
            autogram_obj=import_module_by_file(autogram_file)
            autogram=autogram_obj


        else:

            autogram_compiler=AutogramCompiler()
            autogram_config=AutogramConfig()

            autogram = autogram_compiler(code,config=autogram_config)

            autogram.update_autogram()


      
    elif ext==".csv":

                                
        df=pd.read_csv(autogram_file)
        autogram = Autogram(None,None,{},allow_incomplete=True)

        autogram.add_nodes_from_data_frame(df)
    else:
        raise Exception("invalid autogram file extension "+ext)
    autogram.update_autogram(include_inst=args.label_by_inst)

    graph = autogram.graph.draw_graph(nodes=autogram.nodes,filter_category=args.filter_category)
    graph.format=args.graph_format

    autogram_path = os.path.split(args.autogram_file)
    outname = autogram_path[-1].split(".")[0]



    if args.filter_category is None:
        graph_name=outname+"_full_graph"
    else:
        graph_name = outname+"_" + args.filter_category



    fname=autogram_path[0]+ "/" + graph_name
 

    graph.render(fname).replace('\\', '/')
    # Sample dot string data
    dot_data = {
        'dot_string': graph.source
    }

    graph_node_names = [x[0] for x in autogram.graph.graph_nodes]


    autogram_csv = autogram.convert_to_df()
    fields = autogram_csv.keys()
    csv_dict=dict()
    autogram_keys = list(autogram.nodes.keys())
    for i in range(len(autogram_csv["name"])):
    
        node_dict=dict()

        for field in fields:
            if len(autogram_csv[field][i])>0:
                node_dict[field] = autogram_csv[field][i]
        csv_dict[autogram.nodes[autogram_keys[i]].name]=node_dict






    # Sample node info data
    node_data = get_node_data(autogram,csv_dict,graph_node_names)




    # Generate the variable definitions for dotData and nodeInfo
    dot_data_js = 'var dotData = {dot_string};'.format(dot_string=json.dumps(dot_data))
    node_data_js = 'var nodeInfo = {node_info};'.format(node_info=json.dumps(node_data))

    # # Read the HTML template file
    # with open('template.html', 'r') as file:
    #     html_content = file.read()

    # Replace the placeholders with the generated JavaScript code
    html_content = HTML_TEMPLATE.replace('(((dotData)))', dot_data_js)
    html_content = html_content.replace('(((nodeData)))', node_data_js)

    # Write the modified HTML content to a new file
    with open(fname+ '.html', 'w') as file:
        file.write(html_content)

    print("HTML file generated successfully!")


if __name__ == '__main__':
    main()