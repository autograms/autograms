

import copy
import ast
from collections import OrderedDict
import graphviz
import json
import inspect
import textwrap
import os

def TRANSITION(transition_question,transitions,max_turns=1,ADDRESS=None,**kwargs):
    pass
    # if len(transitions)==1:
    #     new_node_id=transitions[0]
    # else:
    #    # prompt = get_str_history(max_turns=max_turns)
    #     if len(transition_choices)==2 and (transition_choices[0].lower()=="yes" and transition_choices[1].lower()=="no" or transition_choices[1].lower()=="yes" and transition_choices[0].lower()=="no"): 
    #         decision = yes_or_no(question=transition_question,max_turns=max_turns,**kwargs)
    #         if (transition_choices[0].lower()=="yes")==decision:
    #             new_node_id=transitions[0]
    #         else:
    #             new_node_id=transitions[1]

    #     else:
    #         decision = multiple_choice(question=transition_question,choices=transition_choices,max_turns=max_turns,**kwargs)
    #         new_node_id=transitions[decision]

    # transition_exc = process_node_id(new_node_id)

    # raise transition_exc


def convert_to_graph_json(autograms_func):
    tree = copy.deepcopy(autograms_func.processed_def)


def add_function_call_statement(name, kwargs=None):
    """Create a function call statement with keyword arguments."""
    if kwargs is None:
        kwargs = {}
    # Convert the kwargs dictionary into AST keyword nodes
    keyword_args = [ast.keyword(arg=key, value=ast.Constant(value=value)) for key, value in kwargs.items()]
    # Create and return the function call expression
    return ast.Expr(value=ast.Call(func=ast.Name(id=name, ctx=ast.Load()), args=[], keywords=keyword_args))


def add_parent_references(node):
    for child in ast.iter_child_nodes(node):
        child.parent = node
        add_parent_references(child)


def extract_if_branches(node):
    branch_list = []
    is_else=False

    def recurse_if_branches(if_node):
        # Add the current `if` or `elif` branch
        branch_list.append({
            "condition": if_node.test,
            "body": if_node.body
        })
        
        # Check the `orelse` part
        if len(if_node.orelse) == 1 and isinstance(if_node.orelse[0], ast.If):
            # `elif` case: Recurse into the next `If` node in `orelse`
            recurse_if_branches(if_node.orelse[0])
        elif if_node.orelse:
            # `else` case: `orelse` has more than one node or is not an `If`
            nonlocal is_else
            is_else=True
            branch_list.append({
                "condition": None,  # `else` has no condition
                "body": if_node.orelse
            })

    # Start recursion with the initial `If` node
    recurse_if_branches(node)
    return branch_list,is_else

class GraphNode:

    def __init__(self,name,statements=None,conditions=None,transitions=None):

        if statements is None:
            statements=[]
        if conditions is None:
            conditions=[]
        if transitions is None:
            transitions=[]
        self.name = name
        self.statements = statements
        self.conditions= conditions
        self.transitions=list()
        self.open=True
    def set_conditions(self,conditions):
        self.conditions=conditions
       
    def set_transitions(self,transitions):
        self.transitions=[x for x in transitions]
        self.open=False



    def append_statement(self,code):
        if self.open:
            self.statements.append(code)


        #self.transition_dict =transition_dict


# def convert_tree_to_graph_extra(tree):
#     class TreeToGraph(ast.NodeVisitor):
#         def __init__(self):
#             self.graph_nodes={}
#         def visit_If(self, node):
#            # self.graph_nodes.append()

                    
#             branch_list = extract_if_branches(node)
#             if_index = node.parent.body.index(node)

#             decision_switch=False

#             if if_index>0:
#                 prev_node = node.parent.body[if_index - 1]

#                 if (
#                     isinstance(prev_node, ast.assign) and
#                     isinstance(prev_node.value, ast.Expr) and
#                     isinstance(prev_node.value.value, ast.Call) and
#                     isinstance(prev_node.value.value.func, ast.Name)
#                 ):
#                     if prev_node.value.func.id == "multiple_choice" or prev_node.value.func.id == "yes_or_no" or prev_node.value.func.id == "true_or_false":
#                         if len(prev_node.targets)==1:
#                             target = prev_node.targets[0]

#                             for branch in branch_list:
#                                 code = branch["cond"]
#                                 import pdb;pdb.set_trace()


#     add_parent_references(tree)
def extract_function_signature(node):
    if not isinstance(node, ast.FunctionDef):
        raise ValueError("Node is not an ast.FunctionDef")
    
    # Start with the function name
    signature = f"def {node.name}("
    
    # Extract the arguments
    args = []
    total_args = len(node.args.args)
    num_defaults = len(node.args.defaults)
    
    # Arguments with and without default values
    for i, arg in enumerate(node.args.args):
        arg_str = arg.arg  # Argument name
        default_index = i - (total_args - num_defaults)  # Default index in defaults list

        # Append default value if it exists for this argument
        if default_index >= 0:
            default_value = node.args.defaults[default_index]
            if isinstance(default_value, ast.Constant):  # Extract literal default values
                arg_str += f"={repr(default_value.value)}"
            else:
                arg_str += f"={ast.dump(default_value)}"  # Dump AST node for non-constants

        args.append(arg_str)

    # Join arguments with commas
    signature += ", ".join(args) + ")"
    return signature
def extract_value(call_node, arg_kw=None, arg_pos=None):
    if not isinstance(call_node, ast.Call):
        raise ValueError("Node is not an ast.Call")
    
    # Check for keyword argument
    if arg_kw:
        for keyword in call_node.keywords:
            if keyword.arg == arg_kw:
                # Return the literal value if it’s a constant, else the AST node
                return keyword.value.value if isinstance(keyword.value, ast.Constant) else None

    # Check for positional argument
    if arg_pos is not None:
        if 0 <= arg_pos < len(call_node.args):
            arg = call_node.args[arg_pos]
            # Return the literal value if it’s a constant, else the AST node
            return arg.value if isinstance(arg, ast.Constant) else None

    # Return None if the argument isn't found
    return None

def extract_address(node):
        address=None
       
        if isinstance(node,ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            address = extract_value(node.value,"ADDRESS")

        return address

class AutogramsGraph():

    def __init__(self,nodes,name="graph"):
        self.nodes=nodes
        self.name = name
    def save_visualization(self,save_folder,graph_format="png"):


        if not os.path.isdir(save_folder):
            os.mkdir(save_folder)

        save_path = os.path.join(save_folder, self.name)

        from . import HTML_TEMPLATE

        dot_graph = draw_graph(self.nodes)
        dot_graph.format=graph_format


    

        dot_graph.render(save_path).replace('\\', '/')
        # Sample dot string data
        dot_data = {
            'dot_string': dot_graph.source
        }

        graph_node_info = get_node_info(self.nodes)




        # # Generate the variable definitions for dotData and nodeInfo
        # dot_data_js = 'var dotData = {dot_string};'.format(dot_string=json.dumps(dot_data))
        # node_data_js = 'var nodeInfo = {node_info};'.format(node_info=json.dumps(graph_node_info ))

        dot_data_js = 'var dotData = {dot_string};'.format(
            dot_string=json.dumps(dot_data).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        )
        node_data_js = 'var nodeInfo = {node_info};'.format(
            node_info=json.dumps(graph_node_info).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        )

        # Replace the placeholders with the generated JavaScript code
        html_content = HTML_TEMPLATE.replace('(((dotData)))', dot_data_js)
        html_content = html_content.replace('(((nodeData)))', node_data_js)

        # Write the modified HTML content to a new file
        with open(save_path+ '.html', 'w') as file:
            file.write(html_content)

        print("HTML file  generated successfully!")

    def decompile(self,conv_scope="global",globals_to_declare="shared_globals"):

        all_nodes = list(self.nodes.keys())
        root_node= self.nodes[all_nodes[0]]
        function_dec = f'@autograms_function(conv_scope="{conv_scope}",globals_to_declare={globals_to_declare})\n'
        function_def = root_node.statements[0]+":\n"

        body=""
        for node_name in all_nodes[1:]:

            node = self.nodes[node_name]
            text = "\n".join(node.statements)
            if len(node.statements)>0 and "ADDRESS" in node.statements[0]:
                address=extract_address(ast.parse(node.statements[0]).body[0])
            else:
                address=""
            if not address==node_name:
                address_line = f"location(ADDRESS='{node_name}')\n"
                text = address_line+text
            
            print(len(node.transitions))
            transition_code="\n"

            if len(node.transitions)>1:
                transition_code+=f"\nif {ast.unparse(node.conditions[0])}:\n"
                transition_code+=f"   GOTO({repr(node.transitions[0])})\n\n"

                for j in range(1,len(node.transitions)):

                    if len(node.conditions)>j and not node.conditions[j] is None:
                        transition_code+=f"elif {ast.unparse(node.conditions[j])}:\n"
                        transition_code+=f"   GOTO({repr(node.transitions[j])})\n\n"
                    else:
                        transition_code+=f"else:\n"
                        transition_code+=f"   GOTO({repr(node.transitions[j])})\n\n"
            elif len(node.transitions)==1:
                transition_code+=f"\nGOTO({repr(node.transitions[0])})\n\n"
            else:
                transition_code+="\nreturn\n"

            body+=text+transition_code +"\n\n"
        
        indented_code = textwrap.indent(body, "    ")
        code = function_dec+function_def+indented_code
        return code


def compile_graph(func):
    tree = copy.deepcopy(func.processed_def)
    remove_while_loop(tree)
    convert_transition(tree)


    nodes =  convert_tree_to_graph(tree)

    graph = AutogramsGraph(nodes,func.func_name)




    return graph

# def convert_graph_to_tree(graph_nodes):
#     visited = [list(graph_nodes.keys())[0]]
#     root_node= list(graph_nodes.values())[0]
    


#     function_node = ast.parse(function_def).body[0]

#     function_node.body=[]


#     parent_node=function_node

#     next_node = list(graph_nodes.keys())[1]


#     while(len(graph_nodes)<len(visited)):
#         new_body = ast.parse("\n".join(next_node)).body
#         parent_node.extend(new_body)


        





def convert_tree_to_graph(tree):
    class TreeToGraph(ast.NodeVisitor):
        def __init__(self):
          
            self.graph_nodes=OrderedDict()
       
            self.current_node = None
            self.num_nodes=0
            self.auto_node_name="_auto_node"
        def visit_If(self, node):

            if not self.current_node.open:
                self.num_nodes+=1
                new_node_name = self.auto_node_name+str(self.num_nodes)
                new_node = GraphNode(new_node_name)
                self.graph_nodes[new_node_name] = new_node
                self.current_node = self.graph_nodes[new_node_name]

           # self.graph_nodes.append()    
            branch_list,is_else = extract_if_branches(node)


            transitions=[]
            conditions=[]
            graph_branches=[]


            for branch in branch_list:
                cond = branch["condition"]
                conditions.append(cond)
                body = branch["body"]

                if len(body)==1:
                    if (
                        isinstance(body[0], ast.Expr) and
                        isinstance(body[0].value, ast.Call) and
                        isinstance(body[0].value.func, ast.Name) and
                        body[0].value.func.id == "GOTO"
                    ):
                        arg_value=extract_value(body[0].value,"destination",0)

                        if not arg_value is None:
                            transitions.append(arg_value)
                            graph_branches.append(OrderedDict())
                            continue
                #
                # self.num_nodes+=1
                # new_node_name = "node"+str(self.num_nodes)
                # transitions.append(new_node_name)

                orig_node_name=self.current_node.name 

                # new_node = GraphNode(new_node_name)
                # self.graph_nodes[new_node_name] = new_node
                self.current_node.open=False
                

                graph_branch_orig = self.graph_nodes.copy()
                self.graph_nodes=OrderedDict()

                #self.current_node=self.graph_nodes[new_node_name]
                self.num_nodes+=1

                new_node_name = self.auto_node_name+str(self.num_nodes)
                transitions.append(new_node_name)
                new_node = GraphNode(new_node_name)
                self.graph_nodes[new_node_name] = new_node
                self.current_node = self.graph_nodes[new_node_name]


                for child_node in body:
                    self.visit(child_node)
                
                graph_branches.append(self.graph_nodes)
                self.graph_nodes=graph_branch_orig
                self.current_node = self.graph_nodes[orig_node_name]

            self.current_node.set_conditions(conditions)
            self.current_node.set_transitions(transitions)

            if not is_else:
        
                self.current_node.open=True


            for branch in graph_branches:
                self.graph_nodes.update(branch)

            found_open = False
            for graph_node_name in self.graph_nodes:
                graph_node = self.graph_nodes[graph_node_name]
                if graph_node.open:
                    found_open=True
                    break
                


            if found_open:

                self.num_nodes+=1
                new_node_name = self.auto_node_name+str(self.num_nodes)
                new_node = GraphNode(new_node_name)
                
                for graph_node_name in self.graph_nodes:
                    graph_node = self.graph_nodes[graph_node_name]
                    if graph_node.open:
                        graph_node.transitions.append(new_node_name)
                        graph_node.open=False
                

                self.graph_nodes[new_node_name]=new_node
                self.current_node=new_node

                
        def visit_Expr(self, node):
        
         
            #need to appd statement or handle goto
            if   isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "GOTO":
                arg_value=extract_value(node.value,"destination",0)
                if not arg_value is None:
                    self.current_node.set_transitions([arg_value])
                else:
                    self.current_node.set_transitions(["unknown"])

                    
            else:

                address = extract_address(node)
       
                if not(address is None):
                    
                    new_node = GraphNode(address,[ast.unparse(node)])
                    
                    
                    self.graph_nodes[address]=new_node
                    if self.current_node.open:
                        self.current_node.transitions.append(address)
                        self.current_node.open=False
             
                    self.current_node=new_node
                else:
                    if self.current_node.open:
                        self.current_node.append_statement(ast.unparse(node))

        def visit_Assign(self, node):
            #need to appd statement or handle goto
         
            address = extract_address(node.value)
            if not(address is None):
                new_node = GraphNode(address,[ast.unparse(node)])
                
                self.graph_nodes[address]=new_node
                if self.current_node.open:
                    self.current_node.transitions.append(address)
                    self.current_node.open=False

                self.current_node=new_node
            else:
                if self.current_node.open:
                    self.current_node.append_statement(ast.unparse(node))




        def visit_FunctionDef(self, node):
            signature = extract_function_signature(node)
            name = node.name
            body = node.body


            def_node_name = "def_" + name

            def_node = GraphNode(def_node_name,statements=[signature])

            self.num_nodes+=1


            first_node = node.body[0]

            init_address = extract_address(first_node)
            
            if init_address is None:
                self.num_nodes+=1
                init_address = self.auto_node_name+str(self.num_nodes)
                #first_graph_node = GraphNode(init_address,statements=[f"location({init_address})"])
            #else:
            first_graph_node = GraphNode(init_address)

               

            def_node.set_transitions([init_address])
            self.graph_nodes[def_node_name] = def_node

           
            self.graph_nodes[init_address]=first_graph_node 
            self.current_node=first_graph_node

            for node in body:
                self.visit(node)


        def visit_Return(self,node):
            if self.current_node.open:
                self.current_node.append_statement(ast.unparse(node))
                self.current_node.open=False
        # def visit_Try(self,node):


        #     import pdb;pdb.set_trace()

        def generic_visit(self, node):
            if self.current_node.open:
                self.current_node.append_statement(ast.unparse(node))
         

           # return super().generic_visit(node)

    visitor = TreeToGraph()
    visitor.visit(tree)

    return visitor.graph_nodes

def draw_graph(graph_nodes=None):


    dot = graphviz.Digraph(comment='Agent')

    

    for node_name in graph_nodes:
        node = graph_nodes[node_name]


        
        dot.node(node.name,node.name)

        for transition in node.transitions:
            dot.edge(node.name,transition)


    return dot





def get_node_info(graph_nodes):
    node_info=dict()
    for node_name in graph_nodes:
        node = graph_nodes[node_name]
        text = "\n".join(node.statements)
   
        transition_code=""

        if len(node.transitions)>1:
            transition_code+=f"\nif {ast.unparse(node.conditions[0])}:\n"
            transition_code+=f"   GOTO({node.transitions[0]})\n\n"

            for j in range(1,len(node.transitions)):

                if len(node.conditions)>j and not node.conditions[j] is None:
                    transition_code+=f"elif {ast.unparse(node.conditions[j])}:\n"
                    transition_code+=f"   GOTO({node.transitions[j]})\n\n"
                else:
                    transition_code+=f"else:\n"
                    transition_code+=f"   GOTO({node.transitions[j]})\n\n"




        node_info[node.name]=text+"\n"+transition_code
    

    
    return node_info




def get_function_signature(func):
    sig = inspect.signature(func)
    return {param.name: param.default for param in sig.parameters.values() if param.default is not inspect.Parameter.empty}

def get_passed_arguments(call_node):
    args = [arg for arg in call_node.args]  # Positional arguments
    kwargs = {kw.arg: kw.value for kw in call_node.keywords}  # Keyword arguments
    return args, kwargs
def get_all_arguments(func, call_node):
    # Get function signature with defaults
    defaults = get_function_signature(func)
    
    # Get passed arguments
    args, kwargs = get_passed_arguments(call_node)
    
    # Create a mapping for the function arguments
    sig = inspect.signature(func)
    parameters = list(sig.parameters.values())
    
    # Start filling in the arguments
    bound_args = {}
    # Handle positional arguments
    for i, arg in enumerate(args):
        bound_args[parameters[i].name] =ast.unparse(arg)  # Convert AST nodes to actual values
    
    # Handle keyword arguments
    for kw, value in kwargs.items():
        bound_args[kw] = ast.unparse(value)
    
    # Add in any defaults for arguments not provided
    for param in parameters:
        if param.name not in bound_args:
            bound_args[param.name] = defaults.get(param.name)
    
    return bound_args


def convert_transition(tree):
    class FuncProcessor(ast.NodeTransformer):
        def visit_Expr(self, node):

            #need to appd statement or handle goto
            if   isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "TRANSITION":
                kwargs = get_all_arguments(TRANSITION, node.value)
                try:
                    ast_transitions = ast.parse(kwargs['transitions']).body[0].value
                except:
                    import pdb;pdb.set_trace()
           
                choices = repr([x.value for x in ast_transitions.keys])
                transitions = [x.value for x in ast_transitions.values]
                question= kwargs["transition_question"]
                # try:
                #     transitions= ast.literal_eval()
                # except:
                #     return node
                code = f"answer_idx = multiple_choice(question={question},choices = {choices})\n"
                code+= f"if answer_idx == 0:\n   GOTO({repr(transitions[0])})\n\n"

                for i in range(1,len(transitions)):
                    code+= f"elif answer_idx == {i}:\n   GOTO({repr(transitions[i])})\n\n"
               
                return ast.parse(code).body
            else:

                     
               return node
            
    transformer=FuncProcessor()
    transformer.visit(tree)



def remove_while_loop(tree):
    class WhileProcessor(ast.NodeTransformer):
        def __init__(self):
            self.num_while_loops = 0
            self._while_entry_prefix = "while_entry"
            self._while_exit_prefix = "while_exit"
            self.current_entry=None
            self.current_exit=None

        def visit_While(self, node):


            orig_entry = self.current_entry
            orig_exit = self.current_exit
            # Create an `If` node to replace the `While` node
            if_node = ast.If(
                test=node.test,           # Reuse the condition from the `While`
                body=node.body,           # Use the same body as in the `While`
                orelse=[]                 # No `else` clause here
            )
            self.num_while_loops+=1
            address = self._while_entry_prefix+str(self.num_while_loops) 
            self.current_entry=address
            self.current_exit = self._while_exit_prefix+str(self.num_while_loops) 

            new_if_node = self.visit(if_node)


            

            # Create a function call before the `If` statement
            pre_if_call = add_function_call_statement("location",{"ADDRESS":self.current_entry})
            # Create a function call at the end of the `If` body
            end_call = add_function_call_statement("GOTO",{"destination":self.current_entry})
            if_node.body.append(end_call)  # Append it to the end of the `If` body

            after_call = add_function_call_statement("location",{"ADDRESS":self.current_exit})




            self.current_entry=orig_entry
            self.current_exit=orig_exit
            # Replace the `While` node with the `If` node and add the pre-If statement
            return [pre_if_call, new_if_node,after_call]  # Return both nodes to be inserted
        
        def visit_Break(self, node):
             print("breaking")
             break_call = add_function_call_statement("GOTO",{"destination":self.current_exit})
             return break_call
        def visit_Continue(self, node):
            print("continuing")
            continue_call = add_function_call_statement("GOTO",{"destination":self.current_entry})
            return continue_call

    

    # Process the AST
    transformer = WhileProcessor()
    new_tree = transformer.visit(tree)
    print(ast.unparse(new_tree))

    ast.fix_missing_locations(new_tree)  # Ensures line numbers and locations are updated
    return new_tree



def readd_while_loop(tree):
    class InvertIfToWhile(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            # Process the function body
            self.generic_visit(node)


        def visit_If(self, node):
            parent = getattr(node, 'parent', None)
            if not parent:
                return

            # Check if the node before this `If` meets the `location` call condition
            if_index = parent.body.index(node)
            if if_index > 0:
                prev_node = parent.body[if_index - 1]
                if (
                    isinstance(prev_node, ast.Expr) and
                    isinstance(prev_node.value, ast.Call) and
                    isinstance(prev_node.value.func, ast.Name) and
                    prev_node.value.func.id == "location"
                ):
                    for keyword in prev_node.value.keywords:
                        if (
                            keyword.arg == "ADDRESS" and
                            isinstance(keyword.value, ast.Constant) and
                            keyword.value.value.startswith("while_entry")
                        ):
                            # Remove the `location` call and replace `If` with `While`
                            parent.body.pop(if_index - 1)  # Remove the `location` call

                            # Create the `While` node
                            new_while = ast.While(
                                test=node.test,
                                body=node.body[:-1],  # Remove the last node in the body
                                orelse=node.orelse
                            )

                            # Replace the `If` node with the new `While` node
                            parent.body[if_index - 1] = new_while
                            return  # Exit after modifying the structure to prevent multiple visits


    


    # To make this work, we need to ensure each node has a reference to its parent


    add_parent_references(tree)

    # Apply the inversion
    transformer = InvertIfToWhile()
    transformer.visit(tree)
    ast.fix_missing_locations(tree)






# code = """
# def do_stuff():
#     x=1
#     while (x<3):
#       x+=1
#     print('done')
#     print("done2")
 


# """


# code = """
# def do_something(x):
#     while x:
#         if x:
#             if True:
#                 print("hello")
#         elif z>1:
#             print("bye")
#             x=1
#         else:
#             print("what")
# """

code = """
@autograms_function(globals_to_declare=shared_globals, conv_scope='global')
def talk_general():


      if not(lifestory_started):
            lifestory()
                      
            lifestory_started=True


      if not(childhood_complete):
            if not childhood_started:
                  # exec_node(action="chat",
                  #           preprocess_functions = ["set_memory('general')"],
                  #           instruction="Respond to the user. Mention to the user that you'd like to know more about them, and ask if it's alright if you ask some questions about their past",
                  #           transition_question="Is the user okay with discussing their past?", transition_choices=["yes","no"],transitions=["next","ask_preference_general"])
                  childhood_started=True
                  childhood_complete=interview("childhood",False)

            else:
                  set_memory('general')
                  reply_instruction(instruction='Respond to the user. Mention to the user that we have previously discussed their childhood and ask if it is okay if we revisit that discussion')
                  answer_idx = multiple_choice(question='Is the user okay with revisiting the discussion about their past?', choices=['yes', 'no'])
                  if answer_idx==0:
                     pass
                  elif answer_idx==1:
                     GOTO('ask_preference_general')
                  
                  childhood_complete=interview("childhood",True)
          

      if not relationships_complete:
            if not relationships_started:
                  relationships_started=True
                  set_memory('general')
                  reply_instruction(instruction="Respond to the user. Mention to the user that you'd like to learn more about their relationships, and ask if its okay to ask some questions about this.")
                  answer_idx = multiple_choice(question='Is the user okay with discussing their relationships?', choices=['yes', 'no'])
                  if answer_idx==0:
                     pass
                  elif answer_idx==1:
                     GOTO('ask_preference_general')
                  
                  
                  relationships_complete=interview("relationship",False)

            else:

                  set_memory('general')
                  reply_instruction(instruction='Respond to the user. Mention to the user that we have previously discussed their relationships and ask if it is okay if we revisit that discussion')
                  answer_idx = multiple_choice(question='Is the user okay with revisiting the discussion about their relationships?', choices=['yes', 'no'])
                  if answer_idx==0:
                     pass
                  elif answer_idx==1:
                     GOTO('ask_preference_general')
                  
                  
                  relationships_complete=interview("relationship",True)


      if not(identity_complete):
            if not identity_started:
                  identity_started=True
                  set_memory('general')
                  reply_instruction(instruction="Respond to the user. Mention to the user that you'd like to understand their relationship with them self better, and ask if it is okay to ask some questions about their identity.")
                  answer_idx = multiple_choice(question='Is the user okay with discussing their past?', choices=['yes', 'no'])
                  if answer_idx==0:
                     pass
                  elif answer_idx==1:
                     GOTO('ask_preference_general')
                  

                  identity_complete=interview("identity",False)
            else:
                  set_memory('general')
                  reply_instruction(instruction='Respond to the user. Mention to the user that we have previously discussed their childhood and ask if it is okay if we revisit that discussion')
                  answer_idx = multiple_choice(question='Is the user okay with revisiting the discussion about their past?', choices=['yes', 'no'])
                  if answer_idx==0:
                     pass
                  elif answer_idx==1:
                     GOTO('ask_preference_general')
                  

 
                  identity_complete=interview("identity",True)

      if not(hobbies_complete):
            if not hobbies_started:
                  hobbies_started=True
                  set_memory('general')
                  reply_instruction(instruction="Respond to the user. Mention that you'd like to learn more about their hobbies, ask if its alright if you ask some questions about this.")
                  answer_idx = multiple_choice(question='Is the user okay with discussing their past?', choices=['yes', 'no'])
                  if answer_idx==0:
                     pass
                  elif answer_idx==1:
                     GOTO('ask_preference_general')
                  

                  hobbies_complete=interview("hobby",False)
            else:
                  set_memory('general')
                  reply_instruction(instruction='Respond to the user. Mention to the user that we have previously discussed their hobbies and ask if it is okay if we revisit that discussion')
                  answer_idx = multiple_choice(question='Is the user okay with revisiting the discussion about their hobbies?', choices=['yes', 'no'])
                  if answer_idx==0:
                     pass
                  elif answer_idx==1:
                     GOTO('ask_preference_general')
                  

                  hobbies_complete=interview("hobby",True)

      location(ADDRESS='call_recent_events')
      
     

      talk_recent_events()
      RETURNTO('continue_conversation')
      location(ADDRESS='exit_general')



      location(ADDRESS='ask_preference_general')
      set_memory('general')
      reply_instruction(instruction='Ask the user what they would prefer to talk about instead')
      answer_idx = multiple_choice(question='what would the user prefer to talk about?', choices=['An issue they are having', 'recent events in their life', 'other'])
      if answer_idx==0:
         RETURNTO('call_talk_issue')
      elif answer_idx==1:
         GOTO('call_recent_events')
      elif answer_idx==2:
         return
      
      

      RETURNTO('continue_conversation')
      location(ADDRESS='redirect_conv')



"""

# code="""
# @autograms_function(globals_to_declare=shared_globals, conv_scope='global')
# def behavioral_activation(restart):

#       if not beh_started:
            
#             reply_suffix(instruction="Often when we are feeling down or stressed, we stop doing pleasurable and meaningful activities in our life. We might not feel motivated to do those activities we used to like, or we might feel like we don't have time for fun things. The problem with this is that it becomes part of a cycle – our life doesn't have many fun and meaningful activities in it, and that further drags down our mood. Behavioral Activation is a strategy to help break this cycle by planning fun and meaningful activities. To start with, you might not always feel like doing these activities, but by still doing them that is what will help build the behavioral momentum that flows into helping you feel better and having more energy over time. Over time it gets easier, and these activities become a normal and important part of our life. Some people also say “I'm too busy to do fun activities for myself” – but another way to think about this is that, if we don't take some time out for ourselves, we are going to burn out and not be properly productive in those things we are busy with. It’s about balance. Let's consider (1) fun, hobbies, and free time, (2) work and education, (3) relationships, and (4) health and personal development. What is an area that stands out to you that you’d like to work on first?", ADDRESS='b1.c')
#             set_memory('goals')
#             GOTO('b2')
#             beh_started=True
#             #b2 --> b3, b2b
#             reply_suffix(instruction="When setting a goal, it’s best to make sure it’s a SMART goal – meaning it is Specific (a specific behaviour), Measurable (I know when I've done it), Achievable (isn't excessively difficult, or too far away), Relevant (it matters to me), and Time-bound (I set a day and time to do it). For example, I might have the health goal “to get fitter” or “to be fit”, which is great to keep in mind, but it’s a bit vague. To turn that into a SMART goal, let’s break it down into specific behaviors I can do on specific days – I might say instead: “every weekday at 6pm, I'm going to go for a walk around the lake for 30 minutes”. Often it's nice to set goals for activities that we can do regularly each week (e.g., doing at the same time and same day each week), as this helps to build healthy habits in our life. What is an activity that we can set as a SMART goal for this week?", ADDRESS='b2')
#             set_memory('goals')
#             TRANSITION(transitions=['b3', 'b2b'], transition_question="Is the user's goal specific (day and time listed)?", transition_choices=['yes', 'no'])
#             #b2b --> b3
#             reply_instruction(instruction='respond to user and ask if they would prefer to make their goal more specific with a day and time or keep it open', ADDRESS='b2b')
#             set_memory('goals')
#             GOTO('b3')
#             #b3 --> b4, b3b, b3
#             reply_instruction(instruction='respond to user and ask if they would like to set any more goals', ADDRESS='b3')
#             set_memory('goals')
#             set_goals=True
#             TRANSITION(transitions=['b4', 'b3b', 'b3'], transition_question='what did the user do?', transition_choices=['User is done setting goals for now.', 'User set a vague goal without a day and time.', 'User set a specific goal with a day and time.'])
#             #b3b --> b3
#             reply_instruction(instruction='respond to user and ask if they would prefer to make their goal more specific with a day and time or keep it open', ADDRESS='b3b')
#             set_memory('goals')
#             GOTO('b3')
#             #b4 --> t3
#             reply_instruction(instruction='Reply to the user and let them know the goals they have set.', ADDRESS='b4')
#             set_memory('goals')
#             return
            
#       else:
#             if beh_summary is None or restart:
                        
#                   #b1.a --> b11
#                   reply_instruction(instruction='ask the user what area of their life they want to set a goal for. Give them the options (1) fun, hobbies, and free time, (2) work and education, (3) relationships, and (4) health and personal development.', ADDRESS='b1.a')
#                   set_memory('goals')
#                   GOTO('b11')
#                   #b11 --> b3, b2b
#                   reply_instruction(instruction='respond to the user. Ask the user what is a specific and measurable goal we can set in that area.', ADDRESS='b11')
#                   set_memory('goals')
#                   TRANSITION(transitions=['b3', 'b2b'], transition_question="Is the user's goal specific (day and time listed)?", transition_choices=['yes', 'no'])
#             else:
                  
#                   #b1.b --> bc2, bc4
#                   reply_instruction(instruction='list the goals that the user set before, and ask how they are going', ADDRESS='b1.b')
#                   set_memory('goals')
#                   TRANSITION(transitions=['bc2', 'bc4'], transition_question='Does the user feel they are doing a good job with their goals so far?', transition_choices=['yes', 'no'])
#                   #bc2 --> b1.a, bc3
#                   reply_instruction(instruction='encourage the user about their progress, ask if they would prefer to talk more about the existing goals or set new goals', ADDRESS='bc2')
#                   set_memory('goals')
#                   TRANSITION(transitions=['b1.a', 'bc3'], transition_question='Which would the user prefer?', transition_choices=['Setting new goals', 'Talking about existing goals'])
#                   #bc3 --> u1
#                   reply_instruction(instruction='respond to the user, and ask follow up questions about how the user feels about their goals so far', ADDRESS='bc3')
#                   set_memory('goals')

#                   return

# """

# tree = ast.parse(code)
# remove_while_loop(tree)
# convert_transition(tree)
            
# print(ast.unparse(tree))


# graph =  convert_tree_to_graph(tree)

# save_visualization(graph,"test_graph",graph_format="png")

# code=decompile_graph(graph)
# import pdb;pdb.set_trace()
# readd_while_loop(tree)

# print(ast.unparse(tree))