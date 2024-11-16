import os
import subprocess
import tempfile
from .memory import get_memory
from .program_control import FunctionExit, ReturnTo
import dill
import base64
import json
from . import apis
import copy




"""
This is still in beta. it provides a mechanism for an @autograms_function to be called as an external process, potentially with different arguments to change the environment or sandbox the subprocess"

"""

try:
    from cryptography.fernet import Fernet
    encryption_available = True
except ImportError:
    encryption_available = False
    print("Warning: 'cryptography' library not installed. Running without encryption.")
def is_safe_type(obj):
    return isinstance(obj, (int, float, str, bool, type(None), list, dict))

def safe_load(json_data, obj):
    """
    Loads data from JSON and applies it to an existing object in a safe way.
    """
    def decode(data, target):
        if isinstance(data, dict) and "__dict__" in data:
            # This is an object's __dict__ representation
            for key, value in data["__dict__"].items():
                if hasattr(target, key):
                    attr = getattr(target, key)
                    recursive_update(attr, decode(value, attr))
                else:
                    setattr(target, key, decode(value, None))
        elif isinstance(data, dict):
            # Normal dictionary
            return {k: decode(v, None) for k, v in data.items()}
        elif isinstance(data, list):
            return [decode(item, None) for item in data]
        else:
            # Simple types are returned as-is
            return data

    # Parse JSON and recursively update the object
    loaded_data = json.loads(json_data)
    decode(loaded_data, obj)

def recursive_update_safe(x, x_new):
    # Handle dictionaries
    if isinstance(x, dict) and isinstance(x_new, dict):
        for key, value in x_new.items():
            if key in x:
                if x[key] != value:
                    recursive_update(x[key], value)
            else:
                x[key] = copy.deepcopy(value)
    # Handle lists
    elif isinstance(x, list) and isinstance(x_new, list):
        min_len = min(len(x), len(x_new))
        for i in range(min_len):
            if x[i] != x_new[i]:
                recursive_update(x[i], x_new[i])
        if len(x_new) > len(x):
            x.extend(copy.deepcopy(x_new[min_len:]))
    # Handle objects with __dict__ for safe JSON-compatible attributes only
    elif hasattr(x, "__dict__") and hasattr(x_new, "__dict__"):
        for attr, value in x_new.__dict__.items():
            # Check if the attribute in x is safe to update
            if hasattr(x, attr):
                existing_value = getattr(x, attr)
                
                # Only update if both the current and new values are safe types
                if is_safe_type(existing_value) and is_safe_type(value) and existing_value != value:
                    # Recursive update for safe, JSON-compatible nested attributes
                    recursive_update(existing_value, value)
            else:
                # Only set new attributes if they are safe types
                if is_safe_type(value):
                    setattr(x, attr, copy.deepcopy(value))
    # Handle primitives directly, but skip if x is a method or other unsafe type
    elif is_safe_type(x) and is_safe_type(x_new):
        if x != x_new:
            x = x_new  # Note: This only works if `x` is a mutable object, or if x is in a mutable container
def recursive_update_new(x, x_new):
    # Handle dictionaries
    if isinstance(x, dict) and isinstance(x_new, dict):
        for key, value in x_new.items():
            if key in x:
                if x[key] != value:
                    recursive_update(x[key], value)
            else:
                x[key] = copy.deepcopy(value)
    # Handle lists
    elif isinstance(x, list) and isinstance(x_new, list):
        min_len = min(len(x), len(x_new))
        for i in range(min_len):
            if x[i] != x_new[i]:
                recursive_update(x[i], x_new[i])
        if len(x_new) > len(x):
            x.extend(copy.deepcopy(x_new[min_len:]))
    # Handle primitive JSON types: str, int, float, bool, and None
    elif isinstance(x, (str, int, float, bool, type(None))) and isinstance(x_new, (str, int, float, bool, type(None))):
        if x != x_new:
            x = x_new  # Note: this assignment won't affect the caller, so we'll handle it in the next step.
    else:
        # For any unexpected types, we assume x should be replaced by x_new
        x = copy.deepcopy(x_new)

def recursive_update(x, x_new):
    if isinstance(x, dict) and isinstance(x_new, dict):
        for key, value in x_new.items():
            if key in x:
                if x[key] != value:
                    recursive_update(x[key], value)
            else:
                x[key] = value
    elif isinstance(x, list) and isinstance(x_new, list):
        min_len = min(len(x), len(x_new))
        for i in range(min_len):
            if x[i] != x_new[i]:
                recursive_update(x[i], x_new[i])
        if len(x_new) > len(x):
            x.extend(x_new[min_len:])
    elif hasattr(x, "__dict__") and hasattr(x_new, "__dict__"):
        for attr, value in x_new.__dict__.items():
            if hasattr(x, attr):
                existing_value = getattr(x, attr)
                if existing_value != value:
                    recursive_update(existing_value, value)
            else:
                setattr(x, attr,value)
    else:
        # For non-structured types, set x directly to x_new if they differ
        if x != x_new:
            x = x_new



def encrypt_data(data, key):
    fernet = Fernet(key)
    return fernet.encrypt(data.encode())

def decrypt_data(encrypted_data, key):
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data).decode()

def call_worker_script(complex_obj, command_prefix=None,memory_file_name=None,safe_mode=True,key=None):
    # Generate a secure key for encryption if available
    
    if encryption_available and key is None:
        key = Fernet.generate_key()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Determine the directory of this file
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Dynamically construct the module name based on the relative position of `run_subprocess.py`
    package_dir = os.path.dirname(script_dir)  # This assumes `run_subprocess.py` is in `pythonic_autograms`
    package_name = os.path.basename(package_dir)  # e.g., "pythonic_autograms"
    module_name = f"{package_name}.run_subprocess"
   # worker_script_path = os.path.join(script_dir, 'run_subprocess.py')
    clean_memory=False

    if memory_file_name is None:
        memory_file_name = tempfile.mktemp(suffix='.pkl')  # Creates a unique file name only

    # Create temporary files for input and output
    with tempfile.NamedTemporaryFile(delete=False, mode='wb' if encryption_available else 'w+', suffix='.pkl') as input_file, \
         tempfile.NamedTemporaryFile(delete=False, mode='wb' if encryption_available else 'w+', suffix='.pkl') as output_file:
        
        # Serialize the complex object using jsonpickle
        obj_str = dill.dumps(complex_obj)
        serialized_data = base64.b64encode(obj_str).decode('utf-8')
        if encryption_available:
            # Encrypt the serialized data
            encrypted_data = encrypt_data(serialized_data, key)
            input_file.write(encrypted_data)
        else:
            # Write the serialized data directly if not encrypted
            input_file.write(serialized_data)
        input_file.flush()

        try:
            # Prepare the command to run
            command = []
            if command_prefix:
                # Split the prefix into components if provided
                command.extend(command_prefix.split())

            # Add the python call and the worker script
          #  command.extend([worker_script_path , input_file.name, output_file.name,memory_file_name])
            command.extend(["-m", module_name, input_file.name, output_file.name, memory_file_name])
            if encryption_available:
                command.append(key.decode())  # Pass the key as an argument

            # Run the worker script using the assembled command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )

            # Check for errors
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
                output = {"output_type":"error","data":result.stderr}
            else:
                # Read and decode the output from the temporary output file (with the expected suffix)
                
                if os.path.exists(output_file.name):
                    with open(output_file.name, 'rb' if encryption_available else 'r') as f:
                        if encryption_available:
                            encrypted_output = f.read()
                            decrypted_output = decrypt_data(encrypted_output, key)
                   
                            try:
                                output = json.loads(decrypted_output)
                            except:
                                output = {"output_type":"error","data":"all function returns and modifications to inputs must be serializable with json.loads and json.dump"}

                        else:
                            try:
                                output = json.loads(f.read())
                            except:
                                output = {"output_type":"error","data":"all function returns and modifications to inputs must be serializable with json.loads and json.dump"}
                else:
                    print("Error: Output file was not created.")
                    output = {"output_type":"error","data":"no output was created during running of subprocess, something went wrong."}
        
            if output["output_type"]=="return" or output["output_type"]=="error":
                clean_memory=True
                return output,None,None
            else:
                return output,memory_file_name,key
        finally:
            # Clean up temporary files
            os.remove(input_file.name)
            if os.path.exists(output_file.name):
                os.remove(output_file.name)
            if clean_memory:
                if os.path.exists(memory_file_name):
                    os.remove(memory_file_name)

            # if os.path.exists(f"{output_file.name}.processed"):
            #     os.remove(f"{output_file.name}.processed")



class AutogramsSubprocess():
    
    def __init__(self,func_name,module_file=None,source=None,command_prefix="python3",safe_mode=True):
        self.name = func_name
        self.safe_mode=True
        self.command_prefix = command_prefix
        self.module_file = module_file
        if source is None:
            with open(module_file,'r') as fid:
                self.source =fid.read()
        else:
            self.source = source
        


    def __call__(self, *args, **kwargs):
        memory = get_memory()

        print('*******caling subprocess')

        data = {"args":args,"kwargs":kwargs,"root_function_name":self.name,"source":self.source,"api_keys":apis.api_keys,"memory":memory.memory_dict,"config":memory.config}
        # if "turn_stack" in memory.memory_dict.keys():
        #     turn_stack = memory.memory_dict['turn_stack']
        if memory.memory_dict["external_call_memory"] is None:
            memory_file=None
            key=None
        else:
            memory_file=memory.memory_dict["external_call_memory"]['memory_file']
            key=memory.memory_dict["external_call_memory"]['memory_key']


        output,memory_file_name,key = call_worker_script(data,self.command_prefix,memory_file_name=memory_file,key=key)
        

        if memory_file_name is None:
            memory.memory_dict["external_call_memory"] =None
        else:

            memory.memory_dict["external_call_memory"] = {"memory_file":memory_file_name,"memory_key":key}
        

        if output["output_type"]=="return":
          
            memory.memory_dict['turn_stack'][-1]=output["turn_stack"][-1]

            for i in range(len(args)):
                safe_load(output["updated_args"][i],args[i])
            for keyword in range(len(kwargs)):
                safe_load(output["updated_kwargs"][keyword],kwargs[keyword])
                
            return output["data"] 
        elif output["output_type"]=="exit":

            raise FunctionExit(output["data"])

        elif output["output_type"]=="returnto":
            raise ReturnTo(output["data"])     
        
        elif output["output_type"]=="error":
            raise Exception(output["data"])  
        
        else:
            raise Exception("unhandled subprocess")


