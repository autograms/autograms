from ..autogram_utils import get_function
from ..nodes import FunctionNode
import graphviz
import copy







class Graph():
    def __init__(self,graph_nodes,transition_edges,function_call_edges):
        self.graph_nodes = graph_nodes
        self.transition_edges=transition_edges
        self.function_call_edges=function_call_edges


    def filter_by_category(self,nodes=None,filter_category=None):
        if nodes is None or filter_category is None:
            return self.graph_nodes,self.transition_edges,self.function_call_edges
        else:
            transition_edges=[]
            function_call_edges=[]
            graph_nodes=[] 
            all_used = set()

            for edge in self.transition_edges:
                if edge[0] in nodes:
                    if nodes[edge[0]].state_category==filter_category:
                        transition_edges.append(edge)
                        all_used.add(edge[0])
                        all_used.add(edge[1])
            for edge in self.function_call_edges:
                if edge[0] in nodes:
                    if nodes[edge[0]].state_category==filter_category:
                        function_call_edges.append(edge)
                        all_used.add(edge[0])
                        all_used.add(edge[1])


            for node in self.graph_nodes:
                if  node[0] in all_used or (node[0] in nodes and nodes[node[0]].state_category==filter_category):
                    graph_nodes.append(node)



            return graph_nodes,transition_edges,function_call_edges







                        




    def draw_graph(self,nodes=None,filter_category=None):

        dot = graphviz.Digraph(comment='Agent')

        count=1

        graph_nodes,transition_edges,function_call_edges=self.filter_by_category(nodes,filter_category)

        

        for node in graph_nodes:
            
            dot.node(*node)

        

        for edge in transition_edges:
            dot.edge(*edge)


        for edge in function_call_edges:
            dot.edge(*edge,style="dashed")



        return dot

        

        


    





def get_graph(nodes,allow_undefined=True,include_inst=False):
    """
    Simulate transitions.
    """
    graph_nodes=[]
    transition_edges=[]
    function_call_edges=[]

    AZ ="abcdefghijklmnopqrstuvwxyz"
    return_count=0
    quit_count=0

    for node_name in nodes.keys():
        if "(" in node_name:
            arg_str = ",".join(nodes[node_name].args)
            ind = node_name.find("(")
            node_label = node_name[:ind]+"("+arg_str+")"
        else:
            node_label=node_name
        
        if include_inst:
            abrv_inst = nodes[node_name].instruction[:35]
            
            if len(nodes[node_name].instruction)>35:
                abrv_inst+="..."

  

            if len(abrv_inst)>0:
                if "(" in node_name:

                    graph_nodes.append([node_name,node_label+"\n"+abrv_inst])
                else:
                    graph_nodes.append([node_name,abrv_inst])
            else:
                if not(nodes[node_name].boolean_condition is None) and len(nodes[node_name].boolean_condition)>0:
                    graph_nodes.append([node_name,nodes[node_name].boolean_condition])
                else:
                    graph_nodes.append([node_name,node_label])



        else:
            graph_nodes.append([node_name,node_label])
    for node_name in nodes.keys():
        node = nodes[node_name]

        
        
        if isinstance(node,FunctionNode):
            ind = node.instruction.find("(")
   
            if ind<0 and "$" in node.instruction:
                func = "Function call: "+node.instruction
                graph_nodes.append([func,func])
            else:

                if ind<0:

                    raise Exception("invalid function call in function node "+node.name)
            
            
                new_inst = node.instruction[:ind].replace(" ","")+"()"
                func = get_function(new_inst)
                


                if func in nodes.keys():
                    pass
                elif "$" in func:
                    func = "Function call: "+func
                    graph_nodes.append([func,func])
                else:
                    if allow_undefined:
                        func = "Undefined Function: "+func
                        graph_nodes.append([func,func])

                    else:
                        raise Exception("Undefined function call "+node.instruction+" at node " +node_name)

            function_call_edges.append([node_name,func])


    
        transitions = nodes[node_name].transitions
        for state in transitions:
         
            if state[0]=="$":
                var_transition = "Variable node: "+state[1:]
                graph_nodes.append([var_transition,var_transition])
                transition_edges.append([node_name,var_transition])
            elif state[:len("return")]=="return":

                transition_edges.append([node_name,"return"+str(return_count)])
                graph_nodes.append(["return"+str(return_count),state])
                return_count+=1
                
        
            elif state=="quit":
                transition_edges.append([node_name,"quit"+str(quit_count)])
                graph_nodes.append(["quit"+str(quit_count),state])
                quit_count+=1
            elif ".*" in state:
                state_prefix = state.split(".")[0]
                counter=1
                for char in AZ:
                    state_name = state_prefix+"."+char
                    if state_name in nodes.keys():
                        transition_edges.append([node_name,state_name])
                        counter+=1
                    else:
                        if counter<3:

                            if allow_undefined:

                                transition_edges.append([node_name,'undefined_node_'+state_name])
                                graph_nodes.append(['undefined_node_'+state_name,'Undefined Node: '+state_name])
                            else:
                                raise Exception(".* transition for state " + node_name + " must have at least 2 possible transitions.")
                        else:
                            break

            elif ".n" in state:
                state_prefix = state.split(".")[0]
                counter=1
                while True:
                    state_name = state_prefix+"."+str(counter)
                    if state_name in nodes.keys():
                        transition_edges.append([node_name,state_name])
                        counter+=1
                    else:
                        if counter<3:
                            if allow_undefined:
                                transition_edges.append([node_name,'undefined_node_'+state_name])
                                graph_nodes.append(['undefined_node_'+state_name,'Undefined Node: '+state_name])
                            else:
                                raise Exception(".n transition for state " + node_name + " must have at least 2 possible transitions.")
                        else:
                            break
            else:
                if not (state in nodes.keys()):
                    
                    if allow_undefined:
                        transition_edges.append([node_name,'undefined_node_'+state])
                        graph_nodes.append(['undefined_node_'+state,'Undefined Node: '+state])
                    else:
                        raise Exception("Error for state " + str(node_name ) + ". Invalid transition state: " +state)
                else:
                    transition_edges.append([node_name,state])

  
    return  Graph(graph_nodes,transition_edges,function_call_edges)
