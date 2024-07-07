
import json
import os



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
                if not field in ["action","transitions","name","instruction","transition_question"]:
                    if not "transition_choice" in field:
                        node_string+="\n\n" + field + ": "+ str(autogram_csv_dict[node_name][field])


        node_data[node_name]=node_string
                   

    return node_data

def visualize_autogram(autogram,root_path="autogram",filter_category=None,graph_format="png"):

    from . import HTML_TEMPLATE

    graph = autogram.graph.draw_graph(nodes=autogram.nodes,filter_category=filter_category)
    graph.format=graph_format



    if filter_category is None:
        graph_name="_full_graph"
    else:
        graph_name = "_" + filter_category





    fname=root_path+ graph_name
 

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



    # Replace the placeholders with the generated JavaScript code
    html_content = HTML_TEMPLATE.replace('(((dotData)))', dot_data_js)
    html_content = html_content.replace('(((nodeData)))', node_data_js)

    # Write the modified HTML content to a new file
    with open(fname+ '.html', 'w') as file:
        file.write(html_content)

    print("HTML file generated successfully!")