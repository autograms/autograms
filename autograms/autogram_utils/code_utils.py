import ast
#import astor  # Install via pip install astor
import re
import copy
from collections import OrderedDict
SKIP_FLAG_PREFIX= "_AUTO_SKIP_FLAG"
CONDITION_FLAG_PREFIX = "_AUTO_CONDITION_FLAG"
ITERATOR_PREFIX = "_AUTO_ITERATOR"
ITERABLE_PREFIX = "_AUTO_ITERABLE"



debug=False
def set_debug(new_debug=True):

    """
    Enables or disables debug mode for verbose output during AST transformations.

    Parameters:
    - new_debug (bool): True to enable debug mode, False to disable it.
    """
    global debug
    debug=new_debug
    
def check_globals(function_def_node):
    """
    Checks for the presence of global statements in the given function and raises an exception if any are found.

    Parameters:
    - function_def_node (ast.FunctionDef): The function node to inspect.

    Raises:
    - Exception: If a global statement is detected.
    """
    class GlobalStatementVisitor(ast.NodeVisitor):
        def __init__(self):
            pass

        def visit_Global(self, node):
            raise Exception("global keyword not allowed. Global variable declarations should be passed in as set to `globals_to_declare` argument of decorator")
            # Record the line number and the names of the global variables
            self.global_statements.append({
                'line': node.lineno,
                'names': node.names
            })
            # Continue visiting the AST
            self.generic_visit(node)

    visitor = GlobalStatementVisitor()
    # Visit the AST
    visitor.visit(function_def_node)

def declare_globals(source_tree, globals_to_declare):
    """
    Adds a global declaration node as the first statement in the function body.

    Parameters:
    - source_tree (ast.FunctionDef): The function node where globals are declared.
    - globals_to_declare (set or list): Names of variables to declare as global.

    Returns:
    - ast.FunctionDef: A modified function node with global declarations.
    """
    # Create the global declaration node
    function_def_node = copy.deepcopy(source_tree)
    global_node = ast.Global(names=list(globals_to_declare))
    set_line_col(global_node, function_def_node.lineno, function_def_node.col_offset)
    
    function_def_node.body.insert(0, global_node)
    return function_def_node


def get_address_book(function_def_node,func_globals={}):
    """
    Collects addresses from `ADDRESS` arguments in decorated functions for GOTO and RETURNTO.

    Parameters:
    - function_def_node (ast.FunctionDef): The function node to inspect.
    - func_globals (dict): Global context to resolve function references.

    Returns:
    - dict: A dictionary mapping ADDRESS values to line numbers.
    """

    class FunctionCallVisitor(ast.NodeVisitor):
        def __init__(self, keyword_name):
      
            self.keyword_name = keyword_name
            self.matches = dict()

        def visit_Call(self, node):
            # Check if the function name matches the one we're looking for
            if isinstance(node.func, ast.Name):
                
                if node.func.id in func_globals:
                    node_func = func_globals[node.func.id]
             
                    if hasattr(node_func,"_addressable") and node_func._addressable:
                        
                    # Look for the keyword argument
                        for keyword in node.keywords:
                            if keyword.arg == self.keyword_name:
                                # Store the value of the keyword argument
                                value = ast.literal_eval(keyword.value)

                                if not isinstance(value,str):
                                    raise Exception(" `ADDRESS` argument to addressable function must be defined as a string literal. It cannot be a variable.")
                                if keyword.value in self.matches:
                                    raise Exception("all addressable functions called from within a function must have different `ADDRESS` set. `ADDRESS` "+value+"was repeated")
                                self.matches[value]=node.lineno
            
            # Continue traversing the AST
            self.generic_visit(node)

        def get_matches(self):
            return self.matches

    # # Example usage
    # source_code = """
    # def example():
    #     my_function(a=1, b=2)
    #     my_function(c=3, special_key='value')
    #     another_function(special_key='should not match')
    #     my_function(special_key='matched', another=10)
    # """


    # Create the visitor instance for the specific function and keyword you're interested in
    visitor = FunctionCallVisitor( keyword_name='ADDRESS')

    # Visit the AST to find matches
    visitor.visit(function_def_node)

    # Get all matches found
    matches = visitor.get_matches()

    return matches


def find_missing_line_col(node, path="root"):
    """
    Recursively searches for AST nodes missing 'lineno' or 'col_offset'.

    Parameters:
    - node (ast.AST): The root AST node.
    - path (str): Path to the current node, used for debugging.
    """
    if not isinstance(node, ast.AST):
        return

    # Check if the node should have 'lineno' and 'col_offset'
    if hasattr(node, 'lineno') and not hasattr(node, 'col_offset'):
        print(f"Node missing 'col_offset' at path: {path}, node type: {type(node).__name__}, lineno: {node.lineno}")
        print(ast.unparse(node))
        node.lineno=0
    elif hasattr(node, 'col_offset') and not hasattr(node, 'lineno'):
        print(f"Node missing 'lineno' at path: {path}, node type: {type(node).__name__}")
        print(ast.unparse(node))
        node.col_offset=0

    # Recursively check all fields of the node
    for field_name, value in ast.iter_fields(node):
        new_path = f"{path}.{field_name}"
        if isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, ast.AST):
                    find_missing_line_col(item, f"{new_path}[{idx}]")
        elif isinstance(value, ast.AST):
            find_missing_line_col(value, new_path)



def set_line_col_old(node, lineno=None, col_offset=None, verbose=False):
    """
    Recursively sets line number and column offset for AST nodes.

    Parameters:
    - node (ast.AST): The root AST node.
    - lineno (int): Line number to set if missing.
    - col_offset (int): Column offset to set if missing.
    - verbose (bool): If True, logs verbose debug output.
    """
    
    class LineNumberSetter(ast.NodeVisitor):
        def __init__(self, lineno, col_offset, verbose):
            self.lineno = lineno
            self.col_offset = col_offset
            self.verbose = verbose
            self.parent_map = {}

        def visit(self, node):
            if not isinstance(node, ast.AST):
                return

            # Attach parent reference to each child node
            for field_name, value in ast.iter_fields(node):
                if isinstance(value, ast.AST):
                    self.parent_map[value] = node
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            self.parent_map[item] = node

            # Set line and column numbers for the node
            self.set_line_col(node)

            # Recursively visit all child nodes
            super().visit(node)

        def set_line_col(self, node):
            """
            Set line number and column offset for a given AST node, inheriting from the parent if necessary.
            """
            parent = self.parent_map.get(node, None)

            # If node is missing line/column information, inherit from parent or defaults
            if not hasattr(node, 'lineno') or node.lineno is None:
                node.lineno = getattr(parent, 'lineno', self.lineno)
                if self.verbose and node.lineno is None:
                    print(f"Warning: Unable to set line number for {node}")
            if not hasattr(node, 'col_offset') or node.col_offset is None:
                node.col_offset = getattr(parent, 'col_offset', self.col_offset)

            if self.verbose and (node.lineno is None or node.col_offset is None):
                print(f"Node missing line/column info: {type(node).__name__}")
                print(ast.unparse(node) if hasattr(ast, 'unparse') else repr(node))

    # Instantiate and run the LineNumberSetter
    setter = LineNumberSetter(lineno, col_offset, verbose)
    setter.visit(node)

def set_line_col(node, lineno=None, col_offset=None,verbose=False):
    """
    Recursively sets the line number and column offset for a given AST node and all its children.
    Inherits values from parent nodes when appropriate.
    """
    if not isinstance(node, ast.AST):
        return

    # Set lineno and col_offset if they are stmt or expr and do not have these attributes set
 #   if isinstance(node, (ast.stmt, ast.expr)):

    has_info=True

    if not hasattr(node, 'lineno') or node.lineno is None:
        if verbose:
            print("Setting line no")
        node.lineno = lineno
        has_info=False
    if not hasattr(node, 'col_offset') or node.col_offset is None:
        if verbose:
            print("Setting col offset")
        node.col_offset = col_offset
        has_info=False

    #if (isinstance(node,ast.stmt) or isinstance(node,ast.expr)) and not has_info and verbose:
    if not has_info and verbose:
        print("found node missing")
        print(node)
        print(ast.unparse(node))

            

    # Recursively check all fields of the node
    for field_name, value in ast.iter_fields(node):


        if isinstance(value, list):
            
            for item in value:
                if isinstance(item, ast.AST):
                    # Propagate parent's lineno and col_offset to child nodes
                    set_line_col(item, node.lineno, node.col_offset,verbose)
        elif isinstance(value, ast.AST):
            set_line_col(value, node.lineno, node.col_offset,verbose)
# def set_line_col(node, lineno=None, col_offset=None):
#     """
#     Recursively sets the line number and column offset for a given AST node and all its children,
#     but only if they are not already set.
#     """
#     if not isinstance(node, ast.AST):
#         return

#     # Set lineno and col_offset only if they are not already set
#     if hasattr(node, 'lineno') and node.lineno is None:
#         node.lineno = lineno
#     if hasattr(node, 'col_offset') and node.col_offset is None:
#         node.col_offset = col_offset

#     # Iterate over all fields of the node
#     for field_name, value in ast.iter_fields(node):
#         if isinstance(value, list):
#             for item in value:
#                 if isinstance(item, ast.AST):
#                     set_line_col(item, lineno, col_offset)
#         elif isinstance(value, ast.AST):
#             set_line_col(value, lineno, col_offset)

def adjust_line_numbers(node, base_lineno):
    """
    Adjusts the line numbers in an AST node to make them absolute based on the base_lineno.
    """
    for child_node in ast.walk(node):
        if hasattr(child_node, 'lineno'):
            child_node.lineno += base_lineno - 1


def strip_specific_decorator(func_def_node, decorator_names_to_remove):
    """
    Removes specific decorators from a function definition node.

    Parameters:
    - func_def_node (ast.FunctionDef): The function definition node.
    - decorator_names_to_remove (list of str): Names of decorators to remove.

    Returns:
    - ast.FunctionDef: The modified function node.
    """
    # Filter the decorator list to exclude the specified decorator names
    func_def_node.decorator_list = [
        decorator for decorator in func_def_node.decorator_list
        if not (isinstance(decorator, ast.Name) and decorator.id in decorator_names_to_remove)
    ]
    return func_def_node

def remove_decorators(func_def_node):
    """
    Removes all decorators from a function definition node.

    Parameters:
    - func_def_node (ast.FunctionDef): The function definition node.

    Returns:
    - ast.FunctionDef: The modified function node without decorators.
    """
    func_def_node = copy.deepcopy(func_def_node)

    func_def_node.decorator_list = []
    return func_def_node


def modify_function_arguments(func_def_node, new_keywords):
    """
    Modifies the arguments of a FunctionDef AST node to replace them
    with the given list of new keyword arguments. Clears all existing arguments.
    
    Parameters:
    - func_def_node (ast.FunctionDef): The function definition node to modify.
    - new_keywords (list of str): List of new keyword argument names.
    
    Returns:
    - The modified ast.FunctionDef node.
    """
    # Clear all existing arguments in the function definition
    func_def_node.args.args = []  # Positional arguments
    func_def_node.args.kwonlyargs = []  # Keyword-only arguments
    func_def_node.args.vararg = None  # Variable positional arguments (e.g., *args)
    func_def_node.args.kwarg = None  # Variable keyword arguments (e.g., **kwargs)
    func_def_node.args.defaults = []  # Default values for positional arguments
    func_def_node.args.kw_defaults = []  # Default values for keyword-only arguments
    
    # Create new keyword arguments using the new_keywords list
    try:
        new_kwonlyargs = [ast.arg(arg=kw, annotation=None) for kw in new_keywords]
    except:
        import pdb;pdb.set_trace()
    
    # Set the new keyword arguments
    func_def_node.args.kwonlyargs = new_kwonlyargs
    
    # Set the defaults for the keyword-only arguments to None
    # This assumes that all keyword-only arguments have no default value.
    # If you need to provide specific defaults, you can modify this accordingly.
    func_def_node.args.kw_defaults = [None] * len(new_kwonlyargs)
    
    #return func_def_node

class ForToWhileTransformer(ast.NodeTransformer):
    """
    Transforms all `for` loops in an AST into equivalent `while` loops.
    """
    def __init__(self):
        super().__init__()
        self.loop_depth = 0
        self.func_depth = 0 
        
        

    def visit_FunctionDef(self, node):
        # Reset loop depth when entering a new function
        if self.func_depth==0:
            self.func_depth +=1
        
            return self.generic_visit(node)
        else:
            return node

    def visit_For(self, node):
        
        # Increment loop depth for variable naming
        self.loop_depth += 1
        depth = self.loop_depth
        

        # Create names for the iterable and iterator variables based on depth
        iterable_name = f"_auto_iterable_{depth}"
        iterator_name = f"_auto_iterator_{depth}"
        SENTINEL_NAME="_auto_sentinel_string"
        TEMP_ITERATOR= "_auto_tmp_iterator_index"
        

        # Assignment for the iterable
        iterable_assign = ast.Assign(
            targets=[ast.Name(id=iterable_name, ctx=ast.Store())],
            value=node.iter
        )
       # iterable_assign.lineno = node.lineno
        set_line_col(iterable_assign, node.lineno, node.col_offset)

        # Assignment for the iterator
        iterator_assign = ast.Assign(
            targets=[ast.Name(id=iterator_name, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id='iter', ctx=ast.Load()),
                args=[ast.Name(id=iterable_name, ctx=ast.Load())],
                keywords=[]
            )
        )
        set_line_col(iterator_assign, node.lineno, node.col_offset)

        # New while loop condition: while True (we'll break when iterator is exhausted)
        while_loop = ast.While(
            test=ast.Constant(value=True),
            body=[],
            orelse=[]
        )
        

        loop_variable_check = ast.Assign(
            targets=[ast.Name(id=TEMP_ITERATOR,ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id='next', ctx=ast.Load()),
                args=[
                    ast.Name(id=iterator_name, ctx=ast.Load()),
                    ast.Constant(value=SENTINEL_NAME)  # Use SENTINEL_NAME as the fixed sentinel
                ],
                keywords=[]
            )
)

        set_line_col(loop_variable_check, node.lineno, node.col_offset)


        if_check = ast.If(
            test=ast.Compare(
                left=ast.Name(id=TEMP_ITERATOR, ctx=ast.Load()),  # Check loop variable
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=SENTINEL_NAME)]  # Compare with SENTINEL_NAME
            ),
            body=[ast.Break()],  # Break if sentinel is encountered
            orelse=[]
        )
        set_line_col(if_check, node.lineno, node.col_offset)
        

        loop_variable_assign = ast.Assign(
            targets=[node.target],
            value=ast.Name(id=TEMP_ITERATOR, ctx=ast.Load())
)
        set_line_col(loop_variable_assign, node.lineno, node.col_offset)


        # Visit nested nodes if any exist in the while loop body
    # Visit the body of the original for loop and transform any nested loops
        transformed_body = []
        for sub_node in node.body:
            transformed_node = self.visit(sub_node)
            if isinstance(transformed_node, list):
                transformed_body.extend(transformed_node)
            else:
                transformed_body.append(transformed_node)

        # Add the iterator check first
        #mport pdb;pdb.set_trace()
        while_loop.body.append(loop_variable_check)
        while_loop.body.append(if_check)
        while_loop.body.append(loop_variable_assign)
        while_loop.body.extend(transformed_body)

        set_line_col(while_loop, node.lineno, node.col_offset)
        
    

        # Add iterable and iterator assignments before the while loop
        transformed_nodes = [iterable_assign, iterator_assign, while_loop]

        # Reset the loop depth after processing this for loop
        self.loop_depth -= 1

        return transformed_nodes


def convert_for_to_while(source_tree):
    """
    Converts all `for` loops in the AST to `while` loops.

    Parameters:
    - source_tree (ast.AST): The root AST node.

    Returns:
    - ast.AST: The transformed AST.
    """

    copied_tree = copy.deepcopy(source_tree)
    
    transformer = ForToWhileTransformer()
    modified_tree = transformer.visit(copied_tree)
   # ast.fix_missing_locations(modified_tree)
   # set_line_col(modified_tree,0,0,verbose=True)
    # modified_code=astor.to_source(modified_tree)
    # new_tree = ast.parse(modified_code)
   
    # line_mapping=map_line_numbers(tree, new_tree)
    
    return modified_tree #modified_code,line_mapping

def map_line_numbers(original_node, modified_node):
    mapping=dict()

    def map_lines(original_node, modified_node,line_mapping):
        """
        Recursively traverse the original and modified ASTs side by side,
        creating a mapping from the line numbers in the modified tree
        to the line numbers in the original tree.
        """
        # If both nodes have line numbers, map them
        if hasattr(original_node, 'lineno') and hasattr(modified_node, 'lineno'):
            line_mapping[modified_node.lineno]=original_node.lineno

        # Get the children of the nodes
        original_children = list(ast.iter_child_nodes(original_node))
        modified_children = list(ast.iter_child_nodes(modified_node))

        # Traverse children side by side
        for orig_child, mod_child in zip(original_children, modified_children):
            map_lines(orig_child, mod_child, line_mapping)
    map_lines(original_node, modified_node,mapping)

    return mapping

        


def jump_start_function(source_tree, target_line,new_kwargs,include_line=False,globals_to_declare={}):
    """
    Modifies a function's AST to start execution from a specific line.

    Parameters:
    - source_tree (ast.AST): The root AST node of the function.
    - target_line (int): The line number to jump to.
    - new_kwargs (list[str]): New keyword arguments for the function.
    - include_line (bool): Whether to include the target line in execution.
    - globals_to_declare (set): Globals to declare in the function.

    Returns:
    - ast.AST: The modified AST.
    """
    tree = copy.deepcopy(source_tree)
    
    class PathFinder(ast.NodeVisitor):
        """
        Finds the path in the AST to a specific target line.
        """
        def __init__(self, target_line):
            self.target_line = target_line
            self.path = []
            self.found = False
            self.func_depth=0
        def visit_FunctionDef(self, node):
            # Reset loop depth when entering a new function
            if self.func_depth==0:
                self.func_depth +=1
            
                return self.generic_visit(node)
            else:
                return
        def generic_visit(self, node):
            if self.found:
                return
            
            # Check if the node corresponds to the target line
            if hasattr(node, 'lineno') and node.lineno == self.target_line:
                self.found = True
                self.path.append(node)
                return
            
            # Add all nodes to the path
            if not isinstance(node,ast.Module):#(ast.If, ast.While, ast.Expr, ast.Assign, ast.FunctionDef)):
                self.path.append(node)

            # Continue visiting child nodes
            for child in ast.iter_child_nodes(node):
                self.generic_visit(child)
                if self.found:
                    break

            if not self.found and node in self.path:
                self.path.pop()



    class CodeModifier:
        """
        Modifies the AST based on a target path, inserting flags for conditional and loop management.
        """
        def __init__(self, path, target_line):
            self.path = path
            self.target_line = target_line
            self.condition_flags = OrderedDict()
            self.skip_flags = []
            self.original_conditions = []
            self.line_mapping=[]
            self.line_offset=0
            self.statement_map=dict()

        def modify(self):
            # We need one condition flag per conditional (if/while) and one skip flag per indentation level plus one

            modified_nodes = []
            skip_flag_counter = 0
            condition_flag_counter = 0
            self._count_flags()



            if isinstance(self.path[0],ast.FunctionDef):
                modify_function_arguments(self.path[0], new_kwargs)
                
            else:
                raise Exception("attempted to jump start non-function code, this isn't currently enabled")


            new_body = self.process_body(self.path[0].body,skip_flag_counter)
            self.path[0].body=new_body


            skip_flag_counter +=1

            path_it = 1
            while path_it <len(self.path)-1:
                node = self.path[path_it]
                path_it+=1

                

                if isinstance(node, ast.If):

                    #need to check node.orelse, which is basically an alternate body
          

                    if (self.path[path_it]  in node.orelse):
                        self._modify_conditional(node, condition_flag_counter, False)
                        condition_flag_counter+=1
                        body = node.orelse

                    


                        if len(body)==1 and isinstance(body[0],ast.If):
                            continue

                        new_body = self.process_body(body,skip_flag_counter)
                        skip_flag_counter +=1
                        node.orelse=new_body
                        

                    else:
                        self._modify_conditional(node, condition_flag_counter)
                        condition_flag_counter+=1
                        body = node.body

                        new_body = self.process_body(body,skip_flag_counter)
                        skip_flag_counter +=1
                        node.body=new_body
                

                        # if len(body)==1 and isinstance(body[0],ast.If):
                        #     continue

                    
                elif isinstance(node, ast.While):
                    self._modify_conditional(node, condition_flag_counter)
                    condition_flag_counter+=1
                    body = node.body
                    

                    new_body = self.process_body(body,skip_flag_counter)
                    skip_flag_counter +=1
                    node.body=new_body
                    
            
                else:
                    if include_line:
                        raise Exception("Invalid function restart from a transition. This happens from attempting to transition to an invalid branch of a decorated @autograms_function. ADDRESS can only directly be in loops or conditionals. Putting an ADDRESS directly in other types of indents like `with` or `try` `except` can cause this error. Note that it is possible for a node with an ADDRESS to support `try` `except` within its function, you can define new custom nodes that do this using the @autograms_node decorator. You can also put these types of indents in the function that calls the autograms functions. ")

                    else:
                        raise Exception("Invalid function restart from a reply. This happens from a reply statement/exception inside of invalid branch of a decorated @autograms_function. reply functions can only directly be in loops or conditionals in an @autograms_function. Putting a reply directly in other types of indents like `with` or `try` `except` can cause this error. You can either move the reply causing this error, or can wrap the reply in other types of indents by doing this in a non-autograms function that the autograms function calls or is called by.")





            
            self._code_flags(self.path[0].lineno,self.path[0].col_offset)
            self._code_globals(self.path[0].lineno,self.path[0].col_offset)

            if debug:
                print(ast.unparse(source_tree))
      
           # print(astor.to_source(self.path[0]))


                   


            # # Ensure that the modified function body replaces the original one
            # if isinstance(self.path[0], ast.FunctionDef):
            #     self.path[0].body = modified_nodes
        def _count_flags(self):
            num_conditions = sum(1 for node in self.path if isinstance(node, (ast.If, ast.While)))
            for i in range(num_conditions):
                self.condition_flags[f"{CONDITION_FLAG_PREFIX}{i}"]=True
            for i in range(len(path)):
                self.skip_flags.append(f"{SKIP_FLAG_PREFIX}{i}")

        def _code_globals(self,lineno,col_offset):
            if len(globals_to_declare)>0:
                global_node = ast.Global(names=list(globals_to_declare))
                set_line_col(global_node,lineno,col_offset)
                self.path[0].body.insert(0, global_node)


        def _code_flags(self,lineno,col_offset):
            
            # Generate the condition flags and skip flags based on the number of conditionals in the path


            # Add the initializations at the top level
            flag_initializations = []
            for condition_flag in self.condition_flags:
                
                flag_initializations.append(
                    ast.Assign(
                        targets=[ast.Name(id=condition_flag, ctx=ast.Store())],
                        value=ast.Lambda(
                            args=ast.arguments(posonlyargs=[], args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
                            body=ast.Constant(value= self.condition_flags[condition_flag])
                        )
                    )
                )

            for skip_flag in self.skip_flags:
                flag_initializations.append(
                    ast.Assign(
                        targets=[ast.Name(id=skip_flag, ctx=ast.Store())],
                        value=ast.Constant(value=True)
                    )
                )

            for node in flag_initializations:
                set_line_col(node,lineno,col_offset)
                
   

            # Insert these initializations at the start of the function

            self.path[0].body = flag_initializations + self.path[0].body


        def process_body(self,body,skip_flag_idx):

            skipped_body = []
            new_body = []
            found=False
            for node in body:

                if node in self.path :
                    
                        
                    if found:
                        raise Exception("multiple nodes found in body")
                    found=True
                    if node==self.path[-1] and not include_line:
                        skipped_body.append(node)



                    if len(skipped_body)==0:
                        skipped_body = [ast.Pass()]
                        skipped_body[0].lineno = node.lineno
                        #change this so skipped body is ast node representing pass statements



                    new_node = ast.If(
                        test=ast.UnaryOp(op=ast.Not(), operand=ast.Name(id=f"{SKIP_FLAG_PREFIX}{skip_flag_idx}", ctx=ast.Load())),
                        body=skipped_body,
                        orelse=[]
                    )
                   
                    set_line_col(new_node,node.lineno,node.col_offset)

              

                    new_body.append(new_node)
                    if not node==self.path[-1]:
                        new_body.append(node)
                    else:

                        if debug:
                            print("found terminal node!!!!!!!!!!!")

                            

                        reset_body = self._reset_flags()

                        for body_node in reset_body:
                            set_line_col(body_node,node.lineno,node.col_offset)
                        new_body.extend(reset_body)


                        if include_line:
                            new_body.append(node)



                elif found:
                    new_body.append(node)
                else:
                    skipped_body.append(node)

            if not found:
                import pdb;pdb.set_trace()
                raise Exception("node not found")
            
            
    
            

            return new_body





                


                

        def _modify_conditional(self, node, condition_flag_idx,cond_value=True):
            # Save the original condition for the conditional node
            condition_flag = list(self.condition_flags.keys())[condition_flag_idx]

            self.condition_flags[condition_flag]=cond_value

            self.original_conditions.append(node.test)

            # Replace the condition with the condition flag
            node.test = ast.Call(
                func=ast.Name(id=condition_flag, ctx=ast.Load()),
                args=[],
                keywords=[]
            )
            set_line_col(node.test,node.lineno,node.col_offset)
            # node.test.lineno = node.lineno
            # node.test.col_offset = node.col_offset
            
        
            


        def _reset_flags(self):
            
            # Reset all flags immediately after the target line
            modified_nodes=[]
            for i, condition_flag in enumerate(self.condition_flags):
                modified_nodes.append(
                    ast.Assign(
                        targets=[ast.Name(id=condition_flag, ctx=ast.Store())],
                        value=ast.Lambda(
                            args=ast.arguments(posonlyargs=[], args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
                            body=self.original_conditions[i]
                        )
                    )
                )
            for skip_flag in self.skip_flags:
                modified_nodes.append(
                    ast.Assign(
                        targets=[ast.Name(id=skip_flag, ctx=ast.Store())],
                        value=ast.Constant(value=False)
                    )
                )
            return modified_nodes

    # Find the path to the target line
    path_finder = PathFinder(target_line)
    path_finder.visit(tree)
    path = path_finder.path

    if debug:
        import pdb;pdb.set_trace()



    # Modify the code based on the path
    code_modifier = CodeModifier(path, target_line)
    
    code_modifier.modify()
    set_line_col(tree,verbose=False)

    #find_missing_line_col(tree)
    
    


    return tree



def map_line_numbers(original_node, modified_node):
    mapping=dict()

    def map_lines(original_node, modified_node,line_mapping):
        """
        Recursively traverse the original and modified ASTs side by side,
        creating a mapping from the line numbers in the modified tree
        to the line numbers in the original tree.
        """
        # If both nodes have line numbers, map them
        if hasattr(original_node, 'lineno') and hasattr(modified_node, 'lineno'):
            line_mapping[modified_node.lineno]=original_node.lineno
    

        # Get the children of the nodes
        original_children = list(ast.iter_child_nodes(original_node))
        modified_children = list(ast.iter_child_nodes(modified_node))

        # Traverse children side by side
        for orig_child, mod_child in zip(original_children, modified_children):
            map_lines(orig_child, mod_child, line_mapping)
    map_lines(original_node, modified_node,mapping)

    return mapping




