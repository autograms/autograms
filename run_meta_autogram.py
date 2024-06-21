
import random
from collections import OrderedDict
import pandas as pd
import pydot
import json
import re
import ast


from autograms import Autogram, MemoryObject, AutogramConfig, AutogramCompiler

import argparse

class MetaDesignedAutogram():
    def __init__(self,compiler=[]):

        self.nodes=OrderedDict()
        self.undefined_nodes=OrderedDict()
        self.compiler=AutogramCompiler()



    class DefinedNode():
        def __init__(self,node_name,scenario,**kwargs):
            self.name=node_name
            self.scenario = scenario
            self.kwargs=kwargs
      
        

        def __str__(self):
            node_str="Node name: " + self.kwargs["name"]+"\n"
            
            edge_list = [self.kwargs["name"]+" -> " + x for x in self.kwargs["transitions"]]

            node_str+="Node Edges: " +",".join(edge_list)+"\n"
            node_str+="Scenario node handles: "+self.scenario+"\n"

            
            return node_str

    class UndefinedNode():
        def __init__(self,node_name,scenario,parent_scenario):
            self.name=node_name
            self.scenario = scenario
            self.parent_scenario = parent_scenario
    def add_node(self,scenario="",**kwargs):

        name = kwargs["name"]
       

        if "(" in name:
            ind = name.find("(")
            ind2 = name.find(")")
            name[:ind] + "()"

        else:
            name  = name
        self.nodes[name] = self.DefinedNode(name,scenario,**kwargs)

    def get_node_code(node_arg):
        node_code="exec_node("
        arg_strs=[]
        for key in node_arg:
            arg_strs.append(key+"="+node_arg[key])
        
        node_code+=",".join(arg_strs)

        
        node_code+=")\n"

        return node_code


    def add_undefined_node(self,name,scenario,parent_scenario=""):
       
        if "(" in name:
            ind = name.find("(")
            ind2 = name.find(")")
            name[:ind] + "()"

        else:
            name  = name

        self.undefined_nodes[name] = self.UndefinedNode(name,scenario,parent_scenario)

    def pop_node(self,name):
        node = self.undefined_nodes.pop(name)
        return node


    def extract_code(self,reply):

    
        pattern = r'```(\w+)\s+(.*?)\s+```'
        
        # Find all matches of the pattern in the reply
        code_blocks = re.findall(pattern, reply, re.DOTALL)


        return code_blocks[0][1]
    
    def extract_python_code(self,reply):

        
        # Define regex pattern to match Python code blocks
        pattern = r'```python\s+(.*?)\s+```'
        
        # Find all matches of the pattern in the reply
        code_blocks = re.findall(pattern, reply, re.DOTALL)
        
        # Concatenate the code blocks with newline characters
        concatenated_code = '\n'.join(code_blocks)


        if len(concatenated_code)==0:
            return reply

        
        return concatenated_code


    def parse_nodes(self,code):


        nodes = self.compiler(code,return_nodes=True)
        
        
        return nodes


        
    def get_undefined_node_names(self):
        return list(self.undefined_nodes.keys())

    def is_node(self,name):
        return name in self.nodes.keys()
 
    def get_num_total_nodes(self):
        total = len(self.undefined_nodes.keys())+len(self.nodes.keys())
        print("total nodes:",total)
        return total
 

    def get_num_undefined_nodes(self):
        return len(self.undefined_nodes.keys())



    def all_node_repr(self):
        all_node_strs=[]
        for node_name in self.nodes.keys():
            all_node_strs.append(str(self.nodes[node_name]))

        return "\n\n".join(all_node_strs)

    def check_graph(self,dot_source):
        unlabled_nodes=[]
        unlabled_edges=[]
        try:

            dot_graph = pydot.dot_parser.parse_dot_data(dot_source)[0]
            # Extract nodes and their labels

            nodes_with_labels=[]
            nodes_without_labels=[]

            for node in dot_graph.get_nodes():
                if 'label' in node.obj_dict['attributes']:
                    nodes_with_labels.append((node.get_name(), node.get_attributes().get('label')))
                else:
                    nodes_without_labels.append(node.get_name())

            node_names_with_lables=[x[0] for x in nodes_with_labels]
            node_names_without_lables=[x[0] for x in nodes_without_labels]


            
            used_nodes_without_labels=[]
            undefined_nodes=[]

            edges_with_labels=[]
            edges_without_labels=[]
            error_str=""

            for edge in dot_graph.get_edge_list():

                edge_tuple = (edge.get_source(),edge.get_destination(),edge.get_attributes().get('label') )

                if edge_tuple[0] in  node_names_without_lables:
                    used_nodes_without_labels.append(edge_tuple[0])
                elif edge_tuple[0] not in node_names_with_lables:
                    undefined_nodes.append(edge_tuple[0])


                if edge_tuple[1] in  node_names_without_lables:
                    used_nodes_without_labels.append(edge_tuple[1])
                elif edge_tuple[1] not in node_names_with_lables:
                    undefined_nodes.append(edge_tuple[1])


                if 'label' in edge.obj_dict['attributes']:
                    edges_with_labels.append(edge_tuple)
                
                else:
                    edges_without_labels.append(edge_tuple[0]+" -> "+edge_tuple[1])


            if len(undefined_nodes)>0:
                undefined_nodes=list(set(undefined_nodes))
                error_str+="The following nodes used in edges weren't defined:\n"+"\n".join(undefined_nodes)+"\n\n"
                


            if len(used_nodes_without_labels)>0:
                used_nodes_without_labels=list(set(used_nodes_without_labels))
                error_str+="The following nodes used in edges were missing a label:\n"+"\n".join(used_nodes_without_labels)+"\n\n"

            if len(edges_without_labels)>0:
                edges_without_labels=list(set(edges_without_labels))
                error_str+="The following edges were missing a label:\n"+"\n".join(edges_without_labels)+"\n\n"

            return error_str

        except Exception as e:
            return "A problem with the graph syntax led to the following error: "+ str(e)
        

    def parse_transition_args(self,transition_args):


        code=self.extract_python_code(transition_args)


        parsed=ast.parse(code)


        transition_dict=dict()

        for arg in parsed.body[0].value.keywords:
            transition_dict[arg.arg] = ast.literal_eval(arg.value)


        return transition_dict



    def extract_nodes_and_edges(self,dot_source):


        dot_graph = pydot.dot_parser.parse_dot_data(dot_source)[0]
        # Extract nodes and their labels

        nodes_with_labels=[]
        for node in dot_graph.get_nodes():
            if 'label' in node.obj_dict['attributes']:
                nodes_with_labels.append((node.get_name(), node.get_attributes().get('label',"Agent Replies.")))
        

        # Extract edges and their labels
        edges_with_labels = [(
            edge.get_source(),
            edge.get_destination(),
            edge.get_attributes().get('label',"User Replies.")  # Default 'No Label' if label is not present
        ) for edge in dot_graph.get_edge_list()]
        

        node_args=[]

        for node in nodes_with_labels:
            name = node[0]
            agent_reply = node[1]
            transitions=[]
            transition_scenarios=[]
            p_transitions=[]
            p_transition_scenarios=[]

            for edge in edges_with_labels:
                if edge[0]==name:
                    transitions.append(edge[1])
                    transition_scenarios.append(edge[2])

                if edge[1]==name:

                    p_transitions.append(edge[0])
                    p_transition_scenarios.append(edge[2])

            node_args.append({"name":name,"scenario":agent_reply,"transitions":transitions,"transition_scenarios":transition_scenarios,"p_transitons":p_transitions,"p_transiton_scenarios":p_transition_scenarios})
                    

        return node_args

    def init_autogram(self):
        pass




def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--autogram_file', type=str,help='csv or py file with agent')
    parser.add_argument('--api_key_file', type=str,help='json file with api keys.',default=None)
    parser.add_argument('--prompt', type=str,default="Make a chatbot for a recruiter that will ask about salary expectations and start date. The position is a lab tech at a biotech company called Dipply. The salary range for the position is between 50k and 80k, so if the user's expectation is too high let them know this. Be sure to only ask 1 question at a time.")
    parser.add_argument('--outfile_name',type=str,default="meta_designed_autogram.csv")
    args = parser.parse_args()





    if not args.api_key_file is None:
        fid = open(args.api_key_file)
        api_keys = json.load(fid)
        
    else:
        api_keys=dict()

        
    function_dict={"MetaDesignedAutogram":MetaDesignedAutogram,"re":re}


    config = AutogramConfig(python_modules=function_dict,chatbot_path="gpt-4-turbo-2024-04-09",chatbot_generation_args={"temperature":0.1})



    fid = open(args.autogram_file)
    code=fid.read()

    autogram_compiler=AutogramCompiler()



    autogram = autogram_compiler(code,config)

    autogram.update_api_keys(api_keys)
    autogram.allow_incomplete=False
    autogram.update_autogram()


    prompt=args.prompt
    function_args = [prompt]


    result = autogram.apply_fn("design_chatbot()",function_args)

    node_args = [x.kwargs for x in result.nodes.values()]

    new_autogram=Autogram(api_keys=api_keys)
    for node_arg in node_args:
        new_autogram.add_node(**node_arg)

    new_autogram.update_autogram()
    new_df=pd.DataFrame(new_autogram.convert_to_df())


    fname=args.outfile_name

    new_df.to_csv(fname,index=False)



if __name__ == '__main__':
    main()
