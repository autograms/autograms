import ast
from .autogram import Autogram
import pandas as pd

def extract_function_definitions(node,function_dict):
    """
    Recursively traverse AST to find all function definitions in code
    """

    if isinstance(node, ast.Module):
        for stmt in node.body:
            extract_function_definitions(stmt,function_dict)


    elif isinstance(node, (ast.FunctionDef)):
        func_name=node.name
        func_args=[]
        for arg in node.args.args:
            func_args.append(arg.arg)


        if len(node.decorator_list)>0:
            func_type=ast.unparse(node.decorator_list[0])

            if func_type not in ["local_function","global_function","function"]:
                raise Exception("invalid function type (decorator) for "+func_name)


        else:
            func_type="local_function"


        func_chain=AutogramCompilerChain(prefix=func_name+"_")

        func_chain.add_node(name=func_name+"("+",".join(func_args)+")",action="transition")

        function_dict[func_name]= {"function_type":func_type,"function_chain":func_chain,"function_body":node.body}


    else:
        return



def compile_from_ast(node,autogram_compiler_chain):
    """
    Recursive traversal of AST nodes to create AutoGRAMS nodes

    node - AST node in python AST
    autogram_compiler_chain - object for storing and adding AutoGRAMS nodes in the current body of statements

    """
    
    if isinstance(node, ast.Module):
        for stmt in node.body:
            compile_from_ast(stmt,autogram_compiler_chain)

    elif isinstance(node, (ast.ClassDef)):
        raise Exception("no classes allowed")
    elif isinstance(node, (ast.FunctionDef)):
        #handled in extract_function_definitions and defined in autogram compiler. Nested functions not recognized
        pass



    elif isinstance(node, ast.If):

        """
        if AST node is a conditional, create new compiler chain to process body of each conditional, and merge add the new chains to the parent chain with the autogram_compiler_chain.add_conditional() method
        """

  
        cond = ast.unparse(node.test)
     
        conds = [cond]
        sub_chains=[]
        ABCDE="abcdefghijklmnopqrstuvyxyz"
        temp_chain = autogram_compiler_chain.spawn_chain(prefix = "conditional"+str(autogram_compiler_chain.num_conditionals+1)+ABCDE[0]+"_") #AutogramCompilerChain(prefix=autogram_compiler_chain.prefix+"conditional"+str(autogram_compiler_chain.num_conditionals+1)+ABCDE[0]+"_")

        for stmt in node.body:
            compile_from_ast(stmt,temp_chain)
        sub_chains.append(temp_chain)

        # if autogram_compiler_chain.num_conditionals+1==1:

        
            
       

        
        count=0
        
        if len(node.orelse)>0:
            while True:
                count+=1
            
                if isinstance(node.orelse[0], ast.If):
                    node=node.orelse[0]
                    cond_elif = ast.unparse(node.test)
                    conds.append(cond_elif)
                    temp_chain = autogram_compiler_chain.spawn_chain(prefix="conditional"+str(autogram_compiler_chain.num_conditionals+1)+ABCDE[count]+"_")
                
                    for stmt in node.body:
                        compile_from_ast(stmt,temp_chain)
                    sub_chains.append(temp_chain)

                else:
                    
                    temp_chain = autogram_compiler_chain.spawn_chain(prefix="conditional"+str(autogram_compiler_chain.num_conditionals+1)+ABCDE[count]+"_")
                

                    for stmt in node.orelse:
                        compile_from_ast(stmt,temp_chain)
                    sub_chains.append(temp_chain)


                    
                    break


        autogram_compiler_chain.add_conditional(sub_chains,conds)

        
        
        



    elif isinstance(node, ast.For):
        """
        if AST node is forloop, create new compiler chain to process body of forloop, and merge new chain with parent chain in autogram_compiler_chain.add_for_loop method
        """
      
   

        target = ast.unparse(node.target).strip()

        iter = ast.unparse(node.iter).strip()



        temp_chain =autogram_compiler_chain.spawn_chain(prefix="forloop"+str(autogram_compiler_chain.num_for_loops+1)+"_")
        
        for stmt in node.body:
            compile_from_ast(stmt,temp_chain)

        autogram_compiler_chain.add_for_loop(temp_chain,target,iter)
        

    elif isinstance(node, ast.While):
        """
        if AST node is whileloop, create new compiler chain to process body of whileloop, and merge new chain with parent chain in autogram_compiler_chain.add_while_loop method
        """
        

        cond = ast.unparse(node.test)
      
        target_code_lines = []
        

        temp_chain = autogram_compiler_chain.spawn_chain(prefix="whileloop"+str(autogram_compiler_chain.num_loops+1)+"_")
        
        for stmt in node.body:
            compile_from_ast(stmt,temp_chain)



        autogram_compiler_chain.add_while_loop(temp_chain,cond)


        
    elif isinstance(node, (ast.Assign)):
        """
        if AST node is assignment, the assigned variable is parsed out and added to the node's instruction. This adds a single node and returns
        """

        if isinstance(node.value,ast.Call):
            if ast.unparse(node.value.func)=="exec_node":

                
                kwargs=dict()
                for arg in node.value.keywords:

                    kwargs[arg.arg] = ast.literal_eval(ast.unparse(arg.value).strip())

                if "instruction" in kwargs:
                    kwargs["instruction"]=ast.unparse(node.targets[0])+"="+kwargs["instruction"]

                autogram_compiler_chain.add_node(**kwargs)

            elif ast.unparse(node.value.func) in autogram_compiler_chain.functions.keys():
                func_name = ast.unparse(node.value.func)

                if len(node.value.keywords)>0:
                    raise Exception("Functions cannot have key words")
                
                args=list()

                for arg in node.value.args:
                    args.append(ast.unparse(arg))

                action = autogram_compiler_chain.functions[func_name]
          
                instruction = ast.unparse(node.targets[0]).strip()+"="+func_name + "(" + ",".join(args) + ")"


                autogram_compiler_chain.add_node(action=action,name="auto",instruction=instruction)

            else:
                autogram_compiler_chain.add_node(action="python_function",name="auto",transitions=["next"],instruction= ast.unparse(node).strip())

        else:
      
            autogram_compiler_chain.add_node(action="python_function",name="auto",transitions=["next"],instruction= ast.unparse(node).strip())
    elif isinstance(node, ast.Expr):
        """
        if AST node is expression, it is added to the graph. This adds a single to the current chain node and returns.
        """
        if isinstance(node.value,ast.Call):
           
            if ast.unparse(node.value.func)=="exec_node":
                
                kwargs=dict()


                for arg in node.value.keywords:
    
                    

                    kwargs[arg.arg] = ast.literal_eval(ast.unparse(arg.value).strip())
   

                autogram_compiler_chain.add_node(**kwargs)


            elif ast.unparse(node.value.func) in autogram_compiler_chain.functions.keys():

                func_name = ast.unparse(node.value.func)

                if len(node.value.keywords)>0:
                    raise Exception("Functions cannot have key words")
                
                args=list()

                for arg in node.value.args:
         
                    args.append(ast.unparse(arg))

                action = autogram_compiler_chain.functions[func_name]
                instruction = func_name + "(" + ",".join(args) + ")"

                autogram_compiler_chain.add_node(action=action,name="auto",instruction=instruction)


            else:
                
                autogram_compiler_chain.add_node(action="python_function",name="auto",instruction= ast.unparse(node).strip())
        else:
      
            autogram_compiler_chain.add_node(action="python_function",name="auto",transitions=["next"],instruction= ast.unparse(node).strip())

    elif isinstance(node, ast.AugAssign):

        target = ast.unparse(node.target).strip()
        value = ast.unparse(node.value).strip()
        op = node.op
      
        if isinstance(op, ast.Add):
            instruction = target+"="+target +"+"+ value
            autogram_compiler_chain.add_node(action="python_function",name="auto",transitions=["next"],instruction= instruction)
        else:
            raise Exception("augmented assignment not fully handled")
        
    elif isinstance(node,ast.Return):
        """
        Return statements are converted to a return transition from the final node of the function
        """



        if node.value is None:
            autogram_compiler_chain.add_node(action="transition",name="auto",transitions=["return"])

        elif isinstance(node.value,ast.Name):
            autogram_compiler_chain.add_node(action="transition",name="auto",transitions=["return "+ ast.unparse(node.value).strip()])


        else:
            autogram_compiler_chain.add_node(action="python_function",name="auto",transitions=["return"],instruction= ast.unparse(node.value).strip())



    
    else:
        """
        Could reach this if there is an unhandled node
        """
        raise Exception("unhandled abstract syntax tree node type, python code may not be supported by AutoGRAMS compiler")
        
     

    return 


class AutogramCompilerChain():
    """
    Class for building a set of nodes from code
    when encountering if statements and loops, spawns new child chain to define AtuoGRAMS nodes for body of each indent level
    child chains are merged with parent chain using methods specific to forloops, whileloops, and if statements
    """
    def __init__(self,prefix="_",functions={}):
        self.node_args = list()
        self.num_conditionals=0
        self.num_loops=0
        self.num_for_loops=0
        self.prefix=prefix
        self.functions=functions

        

    def add_node(self,**kwargs):
        """
        Add and store the arguments to create a new node
        """
        if not("name") in kwargs or kwargs["name"]=="auto":
            kwargs['name']=self.prefix+"node"+str(len(self.node_args)+1)



        all_names = [x['name'] for x in self.node_args]



        if kwargs['name'] in all_names:
            raise Exception("duplicate node name "+kwargs['name'])


        
           

        if not("transitions") in kwargs:
            kwargs["transitions"]=["next"]
        else:
            if not type(kwargs["transitions"])==list:
                raise Exception("transitions for node "+str(kwargs['name']) +" must be a list")
           
        
        if len(self.node_args)>0 and "next" in self.node_args[-1]['transitions']:
            index = self.node_args[-1]['transitions'].index("next")
            self.node_args[-1]['transitions'][index]=kwargs['name']

        self.node_args.append(kwargs)


    def spawn_chain(self,prefix):
        """
        Defines new child chain. Needs prefix information from parent to know what to call automatically named nodes in child chain
        """
        return AutogramCompilerChain(prefix=self.prefix+prefix,functions=self.functions)

    def add_conditional(self,sub_chains,conds):
        """
        sub_chains - list of chains corresponding to the bodies of each condition in branch
        conds- list of each condition in the branch

        create wildcard transition nodes to handle conditionals.
        """
        self.num_conditionals+=1
        abcde= "abcdefghijklmnopqrstuvwxyz"


        conditional_entrace= self.prefix+"conditional"+str(self.num_conditionals)+"_start"
        end_if_name = self.prefix+"conditional"+str(self.num_conditionals)+"_end"

        if len(self.node_args)>0:

            if "next" in self.node_args[-1]['transitions']:
                index = self.node_args[-1]['transitions'].index("next")
                self.node_args[-1]['transitions'][index]=conditional_entrace
            else:
                if not conditional_entrace in self.node_args[-1]['transitions']:
                    print("Warning!!!! Unreachable conditional after node: "+self.node_args[-1]['name'])

        self.add_node(action="transition",name=conditional_entrace,transitions=[self.prefix+"conditional"+str(self.num_conditionals)+".*"])

        for i in range(len(conds)):
            sub_chain = sub_chains[i].node_args
 

            first_node = sub_chain[0]
            
            
   
            self.add_node(action="transition",name=self.prefix+"conditional"+str(self.num_conditionals)+"."+abcde[i],transitions=[first_node['name']],boolean_condition=conds[i])
            for node in sub_chain:
                self.add_node(**node)
            if "next" in self.node_args[-1]['transitions']:
                index = self.node_args[-1]['transitions'].index("next")
                self.node_args[-1]['transitions'][index]=end_if_name

        if len(sub_chains)>len(conds):


            sub_chain = sub_chains[-1].node_args
        
            first_node = sub_chain[0]
            
            
            self.add_node(action="transition",name=self.prefix+"conditional"+str(self.num_conditionals)+"."+abcde[len(conds)],transitions=[first_node['name']])
            for node in sub_chain:
                self.add_node(**node)

            if "next" in self.node_args[-1]['transitions']:
                index = self.node_args[-1]['transitions'].index("next")
                self.node_args[-1]['transitions'][index]=end_if_name

        else:
            self.add_node(action="transition",name=self.prefix+"conditional"+str(self.num_conditionals)+"."+abcde[len(conds)],transitions=[end_if_name])


        
        self.add_node(action="transition",name=end_if_name)


    def add_while_loop(self,body_chain,cond):
        """
        body_chain - chain corresponding to body of while loop
        cond - exit condition of while loop

        Connects body_chain in loop structure with wildcard transition to facilitate exit
        
        """

        self.num_loops+=1
        while_loop_entrace= self.prefix+"whileloop"+str(self.num_loops)+"_start"
        start_loop_name = self.prefix+"whileloop"+str(self.num_loops)+".a"
        exit_loop_name = self.prefix+"whileloop"+str(self.num_loops)+".b"
        loop_decision_name = self.prefix+"whileloop"+str(self.num_loops)+".*"


        if len(self.node_args)>0:

            if "next" in self.node_args[-1]['transitions']:
                index = self.node_args[-1]['transitions'].index("next")
                self.node_args[-1]['transitions'][index]=while_loop_entrace
            else:
                if not while_loop_entrace in self.node_args[-1]['transitions']:
                    print("Warning!!!! Unreachable while loop after node: "+self.node_args[-1]['name'])


        self.add_node(action="transition",name=while_loop_entrace,transitions=[loop_decision_name])
        first_node = body_chain.node_args[0]
        self.add_node(action="transition",name=start_loop_name,transitions=[first_node['name']],boolean_condition=cond)


        for node in body_chain.node_args:
            self.add_node(**node)
        if "next" in self.node_args[-1]['transitions']:
            index = self.node_args[-1]['transitions'].index("next")
            self.node_args[-1]['transitions'][index]=loop_decision_name
        else:
             if not loop_decision_name in self.node_args[-1]['transitions']:
                print("Warning!!!! Will exit while loop after first iteration after reaching: "+self.node_args[-1]['name'])

        self.add_node(action="transition",name=exit_loop_name)

    def add_for_loop(self,body_chain,target,iter):

        """
        body_chain - chain corresponding to body of for loop
        target - name of forloop iterator
        iter - name of forloop iterable object

        
        """
        self.num_for_loops+=1
        loop_prefix = self.prefix+"forloop"+str(self.num_for_loops)
        init_loop_counter = self.prefix+"forloop"+str(self.num_for_loops)+"_init_counter"
        init_loop_iterable = self.prefix+"forloop"+str(self.num_for_loops)+"_init_iterable"
        get_loop_iterator = self.prefix+"forloop"+str(self.num_for_loops)+"_get_iterator"



        iterate_loop = self.prefix+"forloop"+str(self.num_for_loops)+"_iterate"
        decision_loop_name = self.prefix+"forloop"+str(self.num_loops)+".*"
        start_loop_name = self.prefix+"forloop"+str(self.num_loops)+".a"
        exit_loop_name = self.prefix+"forloop"+str(self.num_loops)+".b"

        if len(self.node_args)>0:

            if "next" in self.node_args[-1]['transitions']:
                index = self.node_args[-1]['transitions'].index("next")
                self.node_args[-1]['transitions'][index]=init_loop_counter
            else:
                print("Warning!!!! Unreachable while loop after node: "+self.node_args[-1]['name'])

        first_node = body_chain.node_args[0]
        self.add_node(action="python_function",name=init_loop_counter,transitions=[init_loop_iterable],instruction=loop_prefix+"_forloop_counter=0")
        self.add_node(action="python_function",name=init_loop_iterable,transitions=[decision_loop_name],instruction=loop_prefix+"_forloop_iterable="+iter)
        self.add_node(action="transition",name=start_loop_name,transitions=[get_loop_iterator],boolean_condition=loop_prefix+"_forloop_counter<len(" + loop_prefix+"_forloop_iterable)")
        self.add_node(action="python_function",name=get_loop_iterator,transitions=[first_node['name']],instruction=target+"="+loop_prefix+"_forloop_iterable["+loop_prefix+ "_forloop_counter]")

        for node in body_chain.node_args:
            self.add_node(**node)
        
        if "next" in self.node_args[-1]['transitions']:
            index = self.node_args[-1]['transitions'].index("next")
            self.node_args[-1]['transitions'][index]=iterate_loop
        else:
             if not iterate_loop in self.node_args[-1]['transitions']:
                print("Warning!!!! Will exit for loop after first iteration after reaching: "+self.node_args[-1]['name'])

        self.add_node(action="python_function",name=iterate_loop,instruction=loop_prefix+"_forloop_counter=" + loop_prefix+"_forloop_counter+1",transitions=[decision_loop_name])
        self.add_node(action="transition",name=exit_loop_name)

        

    def __call__(self,code):

        parsed_code = ast.parse(code)

        extracted_code = []


        compile_from_ast(parsed_code,extracted_code )



class AutogramCompiler():
    def __init__(self):
        pass

        

    def __call__(self,code,config=None,return_nodes=False):

        parsed_code = ast.parse(code)


        function_dict={}

        #find every function defined in the program, add them to function dict. Initialize compiler chain for each function
        extract_function_definitions(parsed_code,function_dict)


        functions = dict()

        for key in function_dict.keys():


            functions[key]=function_dict[key]["function_type"]


        for key in function_dict.keys():

            function_chain = function_dict[key]["function_chain"]
            
            function_chain.functions=functions

            for stmt in function_dict[key]["function_body"]:
                #add nodes for function
                compile_from_ast(stmt,function_chain)

            if len(function_chain.node_args[-1]['transitions'])==1:
                if function_chain.node_args[-1]['transitions'][0]=="next":
                    function_chain.node_args[-1]['transitions'][0]="return"




        compiler_chain = AutogramCompilerChain(functions=functions)
        #create nodes for all code outside of functions 
        compile_from_ast(parsed_code,compiler_chain)
        if len(compiler_chain.node_args)>0:
            if len(compiler_chain.node_args[-1]['transitions'])==1:
                if compiler_chain.node_args[-1]['transitions'][0]=="next":
                    compiler_chain.node_args[-1]['transitions'][0]="quit"

        autogram = Autogram(config,None,{},allow_incomplete=True)



        if return_nodes:
            node_args = []
            for node_arg in compiler_chain.node_args:
                node_args.append(node_arg)
    

            for key in function_dict.keys():

                function_chain = function_dict[key]["function_chain"]
                for node_arg in function_chain.node_args:
                    node_args.append(node_arg)

            return node_args


        else:


            for node_arg in compiler_chain.node_args:
                autogram.add_node(**node_arg)
    

            for key in function_dict.keys():

                function_chain = function_dict[key]["function_chain"]
                for node_arg in function_chain.node_args:
                    autogram.add_node(**node_arg)


            return autogram

