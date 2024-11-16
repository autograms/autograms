import textwrap
import ast
import inspect
import types
from functools import wraps

from .autogram_utils.code_utils import convert_for_to_while, jump_start_function, remove_decorators, get_address_book,adjust_line_numbers,declare_globals, SKIP_FLAG_PREFIX,CONDITION_FLAG_PREFIX
from .memory import get_memory


debug=False
def set_debug(new_debug=True):
    """
    Sets debug mode, can be useful for checking what is going on inside the decorator at specific points.
    
    Parameters:
    - new_debug (bool): If True, enables debug mode. Default is True.
    """
    global debug
    debug=new_debug

def get_dedented_source(source):
    """
    Dedents the provided source code to remove extra indentation.

    Parameters:
    - source (str): The source code as a string.

    Returns:
    - str: Dedented source code.
    """
    dedented_source = textwrap.dedent(source)
    return dedented_source


def filter_variables(variable_dict):
    """
    Filters out internal variables from a variable dictionary.

    Parameters:
    - variable_dict (dict): Dictionary of variables.

    Returns:
    - dict: A filtered dictionary excluding variables with internal prefixes.
    """
    new_variable_dict={}
    for variable in variable_dict:
        if not  SKIP_FLAG_PREFIX in variable and not CONDITION_FLAG_PREFIX in variable:
            new_variable_dict[variable]=variable_dict[variable]

    return new_variable_dict

    

class ControlFlowException(BaseException):
    """
    Base class for control flow exceptions used in Autograms.
    
    Attributes:
    - message (str): A description of the exception.
    """
    def __init__(self,message):
        super().__init__(message)
        


class FunctionExit(ControlFlowException):
    """
    Exception used to signal exiting a function.
    
    Attributes:
    - data (dict): Data passed during function exit.
    """
    def __init__(self, data={}):
        super().__init__(message="Exception for exiting a function")
        self.data=data

        frame_info = find_decorated_frame(3)

        line_number = frame_info.lineno  # Absolute line number in the file
        function_name = frame_info.function
        code_locals = filter_variables(frame_info.frame.f_locals.copy())  # Get a copy of the local variables at the time
      #  code_globals = filter_variables(frame_info.frame.f_globals.copy())  # Get a copy of the global variables at the time

        memory=get_memory()
        memory.process_function_exit(function_name,line_number,code_locals)
        

class ReplyExit(ControlFlowException):
    def __init__(self,reply=None):
        """
        Exception used to pause a chatbot function and return a reply.
        
        Attributes:
        - reply (str): The reply to be returned.

        """

        frame_info = find_decorated_frame()

        message="Exception meant to be used inside autograms functions, meant for pausing the program to return a reply"
     
        super().__init__(message)

        

        # Store information about where the exception occurred

        self.line_number = frame_info.lineno  # Absolute line number in the file
        self.function_name = frame_info.function
        code_locals = filter_variables(frame_info.frame.f_locals.copy())  # Get a copy of the local variables at the time
      #  code_globals = filter_variables(frame_info.frame.f_globals.copy())  # Get a copy of the global variables at the time
 
        memory = get_memory()
        memory.process_function_exit(self.function_name,self.line_number,code_locals)

        self.reply = reply




class  GoTo(ControlFlowException):
    """
    Exception used to jump to a predefined node address.

    Attributes:
    - destination (str): Target node address to jump to.
    """
    def __init__(self,  destination=None):
        # Capture the current stack frame
       # frame = inspect.currentframe().f_back
        frame_info= find_decorated_frame()
        message="Special exception meant to be used inside autograms functions to go to an predefined node address"
     
        super().__init__(message)

        # Store information about where the exception occurred
        self.line_number = frame_info.lineno  # Absolute line number in the file
        self.function_name = frame_info.function
        self.code_locals = filter_variables(frame_info.frame.f_locals.copy())  # Get a copy of the local variables at the time


        self.destination = destination

class  ReturnTo(ControlFlowException):
    """
    Exception used to return to a predefined node address earlier in the call stack.

    Attributes:
    - destination (str): Target node address to return to.
    """
    def __init__(self, destination=None):
        # Capture the current stack frame
       # frame = inspect.currentframe().f_back

        message="ReturnTo exception meant to be used inside autograms functions to go to an predefined node address earlier in the call stack"
       # frame = find_decorated_frame()

     
        super().__init__(message)
        




        self.destination = destination

class  ReturnToContinued(ControlFlowException):
    """
    Continuation of a ReturnTo exception to handle return after an earlier return.

    Attributes:
    - destination (str): Target node address to return to.
    """
    def __init__(self, destination=None):
        message="Special exception meant to be used inside autograms functions to go to an predefined node address earlier in the call stack"
        super().__init__(message)
        self.destination = destination
        #memory = get_memory()
     
       # memory.process_exit_return()
        


def find_decorated_frame(skip_frames=1):
    """
    Finds the previous frame in the call stack containing a decorated function.

    Parameters:
    - skip_frames (int): Number of frames to skip in the stack.

    Returns:
    - inspect.FrameInfo: Frame information for the decorated function.
    """
    stack = inspect.stack()

    # Skip the first two frames:
    # - The first frame is the current call inside __call__ if called from within decorated frame.
    # - The second frame is the decorated function's current execution.
    
    for i, frame_info in enumerate(stack):
        if i < skip_frames:
            continue  # Skip the first two frames

        frame = frame_info.frame
        local_vars = frame.f_locals

        # Check if 'self' in this frame is an instance of our decorator class
        if 'self' in local_vars and isinstance(local_vars['self'], AutogramsFunction):
            
            return stack[i-1]
        


    return None



def get_function_code_object(compiled_object, func_name):
    """
    Retrieves the code object of a specific function from a compiled object.

    Parameters:
    - compiled_object (CodeType): Compiled object containing function code.
    - func_name (str): Name of the function to retrieve.

    Returns:
    - CodeType: Code object of the specified function.

    Raises:
    - ValueError: If the function's code object is not found.
    """


    for const in compiled_object.co_consts:
        # Check if the constant is a code object and has the right name
        if isinstance(const, types.CodeType) and const.co_name == func_name:
            return const
    raise ValueError(f"Function {func_name} code object not found")


def extract_nonlocals(func_orig):
    """
    Extracts nonlocal variables from a function's closure.

    Parameters:
    - func_orig (function): The original function.

    Returns:
    - dict: A dictionary of nonlocal variable names and their values.
    """
    nonlocals = {}
    if func_orig.__closure__:
        # Map free variable names to their cell contents
        free_vars = func_orig.__code__.co_freevars
        nonlocals = {name: cell.cell_contents for name, cell in zip(free_vars, func_orig.__closure__)}
    return nonlocals



def generate_function_from_ast(func_def_node, func_orig,file_name="<ast>"):
    """
    Generates a function object directly from an AST node.

    Parameters:
    - func_def_node (ast.FunctionDef): The AST node of the function definition.
    - func_orig (function): The original function object.
    - file_name (str): Name of the file for error reporting. Default is "<ast>".

    Returns:
    - function: The function object created from the AST node.
    """


    # Compile the AST node into a code object as part of an AST module

    module_node = ast.Module(body=[func_def_node], type_ignores=[])
    module_node.lineno = func_def_node.lineno
    module_node.col_offset = func_def_node.col_offset

   # module_node = ast.fix_missing_locations(module_node)
    #print("fixed")

    compiled_object = compile(module_node, file_name, mode="exec")


    defaults = tuple(func_def_node.args.defaults) if func_def_node.args.defaults else None

    code_object = get_function_code_object(compiled_object, func_def_node.name)


    non_locals = extract_nonlocals(func_orig)
    if len(non_locals)>0:
        raise Exception("function "+func_def_node.name + " cannot be defined inside another function. functions decorated with @autograms_function or @autograms_chatbot must be derived at the module level or directly within a class")
        
    # Create the function object using types.FunctionType
    new_func = types.FunctionType(
        code_object,  # The code object for the function (first constant in the compiled module)
        func_orig.__globals__,
        func_def_node.name,
        defaults,  # Pass the converted tuple here
        None
    )


    return new_func



class AutogramsFunction:


    """
    Represents a function decorated with @autograms_function or @autograms_chatbot.

    Attributes:
    - func_name (str): Name of the decorated function.
    - addresses (dict): Dictionary of node addresses for control flow.
    - processed_function (function): The function after AST processing.
    """

    def __init__(self, func, chatbot=False,conv_scope="global",globals_to_declare={}):
        
        self.globals = func.__globals__
        self.func = func
       
        self.nonlocals = extract_nonlocals(func)
        self.globals_to_declare=globals_to_declare

        self.chatbot=chatbot
        self.conv_scope=conv_scope
        self.sig = inspect.signature(func)
        if self.chatbot:
            self.user_arg_name="user_reply"
            parameters = self.sig.parameters
            if not(self.user_arg_name in parameters):
                raise TypeError(f"Function '{func.__name__}' with @autograms_chatbot decorator must have an argument named '{self.user_arg_name}'")


        self._addressable = getattr(func, '_addressable', False)

        self.func_name = func.__name__
        self.call_memory=None
        _, starting_lineno = inspect.getsourcelines(func)
        source_code =  inspect.getsource(func)
        self.starting_lineno=starting_lineno
        self.source_orig = get_dedented_source(source_code)
        
        
        self.file_name = inspect.getfile(func)

        base_tree=ast.parse(self.source_orig)
      
        
        def_node = base_tree.body[0]
        if not self.starting_lineno is None:
            adjust_line_numbers(def_node,self.starting_lineno)
        self.def_node=def_node

        # Get the source code of the function and compile it
        self.func = func
   
        stripped_tree = remove_decorators(self.def_node)

        while_tree= convert_for_to_while(stripped_tree)

        self.processed_def = while_tree



        self.addresses = get_address_book(self.processed_def,func.__globals__)

        self.processed_function = generate_function_from_ast(while_tree,self.func,self.file_name)

        # print(ast.unparse(while_tree))

        # import pdb;pdb.set_trace()



        # # Compile the modified source code into an executable object
        # self.compiled_code = compile(source, filename="<string>", mode="exec")
        #self._validate_ast()



        #AutogramsFunction.decorated_functions[self.func_name]=self

        
       # self.shared_env.locals[self.func_name]=self

    # def get_child_functions(self):

    #     sub_functions={self.name:self}



    #     def get_functions(sub_functions):
    #         for key in self.func.__globals__:
    #             if isinstance(self.func.__globals__[key],AutogramsFunction):
    #                 sub_functions[key]=self.func.__globals__[key]
    #                 get_functions(self.func.__globals__[key],sub_functions)

    #     get_functions(sub_functions)

    #     return sub_functions
    
    # def update(self,autogram):
    #     self.autogram = autogram



    # def _validate_ast(self):
    #     # Parse the AST of the function
    #     source = inspect.getsource(self.func)
    #     tree = ast.parse(textwrap.dedent(source))
        
    #     # Walk through the AST nodes
    #     for node in ast.walk(tree):
    #         if isinstance(node, ast.Try):
    #             for handler in node.handlers:
    #                 # If the handler catches `BaseException` or is a generic `except:`
    #                 if handler.type is None or (
    #                     isinstance(handler.type, ast.Name) and handler.type.id == "BaseException"
    #                 ):
    #                     # Check if it specifically handles ReplyExit
    #                     if not self._is_handling_special_exit(handler):
    #                         raise ValueError(
    #                             f"Function '{self.func_name}' contains a disallowed generic or BaseException handler. This interferes with return mechanism for replies"
    #                         )
    #                 elif isinstance(handler.type, ast.Name):
    #                     # If the handler catches a subclass of Exception, it's fine
    #                     if handler.type.id == "Exception" or issubclass(eval(handler.type.id, {}, {}), Exception):
    #                         continue
    #                     # If the handler catches another specific BaseException subclass
    #                     elif issubclass(eval(handler.type.id, {}, {}), BaseException):
    #                         if handler.type.id != "ReplyExit":
    #                             # If it's not ReplyExit, allow it
    #                             continue
    #                     else:
    #                         raise ValueError(
    #                             f"Function '{self.func_name}' contains a disallowed exception handler: {handler.type.id}"
    #                         )

    # def _is_handling_special_exit(self, handler):
    #     """Check if the except handler specifically handles ReplyExit."""
    #     if handler.type is None:
    #         return False  # A generic except: block
    #     if isinstance(handler.type, ast.Name) and handler.type.id == "ReplyExit":
    #         return True
    #     return False
    # def _get_stripped_source(self):
    #     # Get the source code of the function
    #     source = self.source_orig

    #     # Split the lines of the source code
    #     source_lines = source.splitlines()

    #     # Remove lines that start with @ (which are decorators) until the function definition
    #     line_mapping = dict()
    #     stripped_lines = []

    #     for i in range(len(source_lines)):
    #         line = source_lines[i]
    #         if not line.strip().startswith('@'):
    #             line_mapping[len(stripped_lines)]=i
    #             stripped_lines.append(line)

                

      #  stripped_lines = [line for line in source_lines if not line.strip().startswith('@')]

        # Join the remaining lines and dedent the code
        # stripped_source = textwrap.dedent("\n".join(stripped_lines))
        # return stripped_source,line_mapping
        

    def __call__(self, *args, **kwargs):
        """
        Executes the decorated function, managing control flow and memory.

        Returns:
        - AutogramsReturn: Object containing return value, memory, and additional data.
        """
        last_frame = find_decorated_frame(2)

        if last_frame is None:

            root_call=True
        else:
            root_call=False
            if self.chatbot:
                raise Exception("function defined with @autograms_chatbot decorator must be called externally. Use @autograms_function for functions that must be called from within other autograms functions or chatbots")

        memory = get_memory()

        if self.chatbot:      
            bound_args = self.sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Extract 'user_reply' if it exists
            user_reply = bound_args.arguments.get(self.user_arg_name, None)
            if not (user_reply is None):
                memory.add_user_reply(user_reply)



        call_info,include_line = memory.process_call(last_frame,self.conv_scope)

        done = False
        if call_info is None:
            target_line=None
            code_locals={}
            include_line=False
        else:
            target_line=call_info['line_number']
            code_locals=call_info['locals']


        if not target_line is None and self.chatbot:

            for arg_name in bound_args.arguments:
                code_locals[arg_name] =  bound_args.arguments[arg_name]

        
        while not done:

            
            
            if target_line is None:
                if len(self.globals_to_declare)==0:
                    function_obj = self.processed_function
                else:
                    function_tree = declare_globals(self.processed_def,self.globals_to_declare)
                    function_obj = generate_function_from_ast(function_tree,self.func,self.file_name)

      
            else:

                function_tree = jump_start_function(self.processed_def,target_line,code_locals.keys(),include_line,globals_to_declare=self.globals_to_declare)

                function_obj = generate_function_from_ast(function_tree,self.func,self.file_name)
                #line_mapping_full = merge_line_mapping(line_mapping,self.line_mapping)
                args =[]
                kwargs = code_locals

         #   import pdb;pdb.set_trace()
            try:
      
                result =  function_obj(*args, **kwargs)

                done=True

                


            except ReplyExit as reply_exc:    
                done=True


                if root_call:
                    memory=get_memory()
                    return AutogramsReturn(func_return=None,memory=memory,data={"reply":reply_exc.reply})
                else:
                    if debug:
                        import pdb;pdb.set_trace()


                    raise FunctionExit(data ={"reply":reply_exc.reply})
            
            except FunctionExit as exc_cont:
                done=True

                if debug:
                    import pdb;pdb.set_trace()
                if root_call:
                    memory=get_memory()
                
                    return AutogramsReturn(func_return=None,memory=memory,data=exc_cont.data)
                else:

                    raise FunctionExit(data =exc_cont.data)    
            except ReturnTo as rt_exc:

                if root_call:
                    raise Exception("error caused by invalid ReturnTo exit, destination " +str(rt_exc.destination)+" not found in defined addresses in stack" )
                else:
                    memory.process_return()
                    raise ReturnToContinued(destination=rt_exc.destination)
                
            except ReturnToContinued as rt_exc:
                if rt_exc.destination in self.addresses:
                    target_line = self.addresses[rt_exc.destination]
                else:
                    if root_call:
                        raise Exception("error caused by invalid ReturnTo exit, destination " +str(rt_exc.destination)+" not found in defined addresses in stack" )
                    else:
                        memory.process_return()
                        raise ReturnToContinued(destination=rt_exc.destination)

            except GoTo as jump_exc:
                if jump_exc.destination in self.addresses:
                    target_line = self.addresses[jump_exc.destination]
                    code_locals = jump_exc.code_locals
                    include_line=True


                else:
                    import pdb;pdb.set_trace()
                    raise Exception("Error caused by invalid transition to unknown address: "+jump_exc.destination)
                
        memory.process_return()
        if root_call:
            memory=get_memory()
            return AutogramsReturn(func_return=result,memory=memory,data={"reply":None})
        
        else:
            return result


    

class AutogramsReturn():
    """
    Represents the return value of an Autograms function call.

    Attributes:
    - func_return: The function's return value.
    - memory: MemoryObject containing the program's state.
    - data (dict): Additional data including replies.
    """
    def __init__(self,func_return,memory,data={}):
        self.func_return=func_return
        self.memory = memory
        self.data =data

def autograms_function(conv_scope="global",globals_to_declare={}):
    """
    Decorator for defining an Autograms function.

    Parameters:
    - conv_scope (str): Conversation scope for the function.
    - globals_to_declare (dict): Global variables to declare in the function.
    """
    def decorator(func):
        return AutogramsFunction(func,conv_scope=conv_scope,globals_to_declare=globals_to_declare)
    
    return decorator


def autograms_chatbot(conv_scope="global",globals_to_declare={}):
    """
    Decorator for defining a chatbot function.

    Parameters:
    - conv_scope (str): Conversation scope for the chatbot.
    - globals_to_declare (dict): Global variables to declare in the function.
    """
    def decorator(func):

        return AutogramsFunction(func,chatbot=True,conv_scope=conv_scope,globals_to_declare=globals_to_declare)
    
    return decorator



def autograms_node(func):
    """
    Decorator for defining addressable nodes in Autograms.

    Parameters:
    - func (function): The function to decorate.

    Returns:
    - function: The decorated function with addressable memory for control flow.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "ADDRESS" in kwargs.keys():
            memory = get_memory()
            with memory.set_node(kwargs["ADDRESS"]):  # Enter context manager
                return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
        
    wrapper._addressable = True 


    return wrapper



