import operator
import ast
import importlib

def add_submodules(module,module_name,callable_fns,depth=0,max_depth=3):
    
    if callable(module):
        callable_fns[module_name]= module
        

        
    submodules = dir(module)
   
      
    contains__ = [x[:2] == "__" for x in submodules]


    if "__" in module_name or all(contains__) or depth==max_depth:
        return
    else:
        for mod in submodules:
            try:
                getattr(module,mod)
            except:
                continue
            add_submodules(getattr(module,mod),module_name+"."+mod,callable_fns=callable_fns,depth=depth+1,)


def get_operator(op_name):
    if op_name=="div":
        op_function = getattr(operator, "truediv")
    elif op_name=="noteq":
        op_function = getattr(operator, "ne")
    elif op_name=="is":
        op_function = getattr(operator, "is_")
    elif op_name=="isnot":
        op_function = getattr(operator, "is_not")

    else:
        op_function = getattr(operator, op_name)
    return op_function

class Disallowed():
    def __init__(self,name):
        self.name=name


    def __call__(self,*args,**var_args):
        raise Exception(self.name + " not allowed")
    
class APIWrapper():

    def __init__(self,name,api_key,function):
        self.api_key = api_key
        self.name=name
        self.function = function
    def __call__(self,*args,**var_args):
        return self.function(*args,api_key=self.api_key,**var_args)


def dynamic_import(statements):
    # Dictionary to hold the isolated execution environment
    exec_env = {}
    
    # Execute each import statement in the isolated environment
    for statement in statements:
        exec(statement, {}, exec_env)
    
    # Create a dictionary with the imported names and their corresponding objects
    imported_dict = {name: obj for name, obj in exec_env.items()}
    
    return imported_dict

class StatementInterpreter():

    def __init__(self,autogram_config,api_keys={}):

        self.modules={}
        self.disallowed_built_ins = {}
        self.reference_memory_object=autogram_config.reference_memory_object

        all_built_ins = dir(globals()['__builtins__'])
        for module_name in all_built_ins:
            if module_name in autogram_config.python_built_ins:
                continue
            else:
                self.disallowed_built_ins[module_name]=Disallowed(module_name)


        imported_modules = dynamic_import(autogram_config.python_imports)


        for mod_name in imported_modules.keys():

            self.modules[mod_name]=imported_modules[mod_name]
      

        for key in autogram_config.python_modules.keys():
            if key in api_keys.keys():
                self.modules[key].api_key = api_keys[key] #=APIWrapper(key,api_keys[key],autogram_config.python_modules[key])

            else:
                self.modules[key]=autogram_config.python_modules[key]








    def execute_expression(self,code, variables):

        

        locals_dict = {**variables,**self.modules,**self.disallowed_built_ins}
        try:
            output=eval(code, {}, locals_dict)
        except Exception as exc:
            import pdb;pdb.set_trace()
            raise Exception("Python function node with code: "+str(code) +" failed with exception "+str(exc))




        return output
    
    def execute_assignment(self,code, variables):
      
        module = ast.parse(code)
        if isinstance(module.body[0],ast.Assign):
            var_name = module.body[0].targets[0].id
            expression = module.body[0].value
            # Reconstruct the expression as a string
            expression_code = ast.unparse(expression)
        else:
            var_name=None
            expression_code =code

        locals_dict = {**variables,**self.modules,**self.disallowed_built_ins}

  
        output=eval(expression_code, {}, locals_dict)



        return var_name, output








        

