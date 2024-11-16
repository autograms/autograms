import jsonpickle
import sys


import json 
import dill
import base64
import os
import importlib
import tempfile



try:
    from cryptography.fernet import Fernet
    encryption_available = True
except ImportError:
    encryption_available = False



from .memory import MemoryObject

from . import Autogram

def decrypt_data(encrypted_data, key):
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data).decode()

def encrypt_data(data, key):
    fernet = Fernet(key)
    return fernet.encrypt(data.encode())



def safe_save(obj):
    """
    Safely serializes an object to JSON, encoding __dict__ as a tagged structure
    to distinguish it from ordinary dictionaries.
    """
    def encode(value):
        if isinstance(value, dict):
            # Distinguish __dict__ from regular dicts
            return {
                "__dict__": {k: encode(v) for k, v in value.items()}
            }
        elif isinstance(value, list):
            return [encode(item) for item in value]
        elif isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif hasattr(value, "__dict__"):
            # Recursively save the object's __dict__ with a distinguishing tag
            return {"__class__": value.__class__.__name__, "__dict__": encode(value.__dict__)}
        else:
            raise TypeError(f"Unsupported type: {type(value)}")

    # Begin by encoding the main object
    return json.dumps(encode(obj), indent=2)
def load_function_with_exec(code, function_name):
    """Dynamically load a function from a Python file using exec.

    Args:
        file_path (str): Path to the Python file.
        function_name (str): Name of the function to extract.

    Returns:
        function: The extracted function.
    """
    global_namespace = {}
    local_namespace = {}
    
    # # Read the file content
    # with open(file_path, "r") as file:
    #     code = file.read()
    
    # Execute the code in a clean namespace
    exec(code, global_namespace, local_namespace)
    
    # Extract the function
    func = global_namespace.get(function_name) or local_namespace.get(function_name)
    
    # if not callable(func):
    #     raise ValueError(f"Function '{function_name}' not found in {file_path}.")
    
    return func
def load_module_from_string(source_code, module_name):
    # Write the source code to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
        temp_file.write(source_code.encode())
        temp_file_path = temp_file.name

    # Load the module from the temporary file
    spec = importlib.util.spec_from_file_location(module_name, temp_file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Remove the temporary file
    os.remove(temp_file_path)
    return module

def run_autogram(input_file_path,output_file_path,memory_file_path,key):

    with open(input_file_path, 'rb' if key else 'r') as f:
        if key:
            encrypted_data = f.read()
            text = decrypt_data(encrypted_data, key)
            
        else:
            text = f.read()




         

    recovered_data= base64.b64decode(text)
    data = dill.loads(recovered_data)



    if os.path.isfile(memory_file_path):
        with open(memory_file_path, 'rb' if key else 'r') as f:
            if key:
                encrypted_data = f.read()
                text = decrypt_data(encrypted_data, key)
                
            else:
                text = f.read()
        recovered_data= base64.b64decode(text)
        memory_dict = dill.loads(recovered_data)

         
    else:

    

        memory_dict = data['memory']

        memory_dict["external_call"]=None
        memory_dict['stack']=[]
   
        memory_dict['stack_pointer']=-1
        memory_dict['call_depth']=0
        memory_dict['globals_snapshot']={}


   

    


    
    

    function_name = data['root_function_name']
    source = data['source']

    module = load_module_from_string(source, "temp_module")
    func_obj = getattr(module, function_name)



    autogram = Autogram(root_function=func_obj,autogram_config = data['config'],api_keys=data['api_keys'])

    args=data['args']
    kwargs = data['kwargs']
    with autogram.use_memory(memory_dict=memory_dict):
        result = func_obj(*data['args'],**data['kwargs'])

    with open("log",'w') as fid:
        fid.write(f"hello from subprocess {result.func_return}")
    data_output = {"turn_stack":memory_dict['turn_stack']}
    if result.data['reply'] is None:
        data_output["output_type"]="return"
        data_output["data"] = result.func_return

        updated_args = [None]*len(args)

        for i in range(len(args)):

            updated_args[i] = safe_save(args[i])


        updated_kwargs=dict()
        for key in kwargs:

            updated_kwargs[key] = safe_save(kwargs[key])

        data_output["updated_args"]= updated_args
        data_output["updated_kwargs"]= updated_kwargs



    else:
        memory_str = dill.dumps(memory_dict)
        memory64= base64.b64encode(memory_str).decode('utf-8')

        
        
        with open(memory_file_path, 'wb' if key else 'w') as f:
            if key:
                encrypted_memory = encrypt_data(memory64, key)
                f.write(encrypted_memory)
                
                
            else:
                f.write(memory64)


        data_output["output_type"]="exit"
        data_output["data"]=result.data



    

    data_json = json.dumps(data_output)

    encrypted_output = encrypt_data(data_json, key)

    with open(output_file_path, 'wb' if key else 'w') as f:
        if key:
            
            f.write(encrypted_output)
        else:
            f.write(data)




    

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: run_subprocess.py <input_file> <output_file> <memory_file> [encryption_key]", file=sys.stderr)
        sys.exit(1)

    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]
    memory_file = sys.argv[3]
    key = sys.argv[4].encode() if len(sys.argv) == 5 else None
    run_autogram(input_file_path,output_file_path,memory_file,key)