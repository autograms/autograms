
import ast




class Disallowed():
    def __init__(self,name):
        self.name=name


    def __call__(self,*args,**var_args):
        raise Exception(self.name + " not allowed")
    



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

            if mod_name in api_keys.keys():
                self.modules[mod_name].api_key = api_keys[mod_name]
      

        for key in autogram_config.python_modules.keys():

            self.modules[key]=autogram_config.python_modules[key]
            if key in api_keys.keys():
                self.modules[key].api_key = api_keys[key] 

            if hasattr(autogram_config.python_modules[key], "api_key_name"):
                api_key_name = getattr(autogram_config.python_modules[key], "api_key_name")
                if api_key_name in api_keys.keys():
                    self.modules[key].api_key = api_keys[api_key_name]





    def execute_expression(self,code, variables):

        

        locals_dict = {**variables,**self.modules,**self.disallowed_built_ins}
        
        try:
            output=eval(code, {}, locals_dict)
        except Exception as exc:
            
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








        

