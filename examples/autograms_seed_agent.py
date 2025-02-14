
import autograms
from autograms import autograms_function

from autograms.nodes import location
from autograms.functional import multiple_choice, yes_or_no,reply,thought,yes_or_no, generate_list, extract_code,reply_instruction,set_system_prompt, GOTO
import os
import inspect

from datetime import datetime



REPOSITORY_ROOT="./"



email = "bkrause@autograms.ai"
name="Ben Krause"



def compare_versions(v1, v2):
    """Compares two version strings, returns True if v1 < v2."""
    v1_parts = [int(part) for part in v1.split('.')]
    v2_parts = [int(part) for part in v2.split('.')]
    return v1_parts < v2_parts

# Required version
required_version = "0.5.2"

# Check if the installed version is outdated
if compare_versions(autograms.__version__, required_version):
    raise Exception(
        f"autograms version {autograms.__version__} cannot run this version of Asa. "
        f"Please upgrade to version >= {required_version} using:\n\n"
        f"    pip install 'autograms>={required_version}'"
        "or clone the latest repository with:"
        "     git clone https://github.com/autograms/autograms.git" 
        "and use:" 
        "     pip install ."
        "from the root directory"
    )



def extract_docs():
    """
    Extract markdown documentation files into a dictionary.
    
    Returns:
    - dict: A dictionary mapping file names to their markdown content.
    """
    docs = {}
    paths = [
        os.path.join(REPOSITORY_ROOT, "README.md"),
        os.path.join(REPOSITORY_ROOT, "docs", "index.md"),
    ]
    # Include all markdown files in /docs/documents
    doc_folder = os.path.join(REPOSITORY_ROOT, "docs", "documents")
    if os.path.isdir(doc_folder):
        paths += [
            os.path.join(doc_folder, f)
            for f in os.listdir(doc_folder)
            if f.endswith(".md")
        ]

    for path in paths:
        if os.path.exists(path):
            with open(path, "r") as file:
                docs[os.path.basename(path)] = file.read()
        else:
            raise Exception("must run Asa from autograms repository root directory so it can find docs.")
    return docs


def extract_examples():
    """
    Extract Python example files from the /examples folder into a dictionary.
    
    Returns:
    - dict: A dictionary mapping file names to their Python source code.
    """
    examples_dir = os.path.join(REPOSITORY_ROOT, "examples")
    examples = {}
    if os.path.isdir(examples_dir):
        for file in os.listdir(examples_dir):
            if file.endswith(".py") and file != "__init__.py":
                with open(os.path.join(examples_dir, file), "r") as f:
                    examples[file] = f.read()
    return examples



def extract_modules():
    """
    Recursively extract all modules from the `autograms` package using the module object.
    
    Returns:
    - dict: A dictionary mapping module names to their source code.
    """
    processed = set()  # Track processed modules to avoid infinite recursion
    modules = {}

    def process_module(module):
        if module in processed or not module.__name__.startswith("autograms"):
            return
        processed.add(module)
        try:
            # Only attempt to get source if the file exists and is not a directory
            file = inspect.getfile(module)
            if os.path.isfile(file):
                source = inspect.getsource(module)
                modules[module.__name__] = source
            else:
                print(f"Skipping module {module.__name__}: Not a valid file")
        except (TypeError, OSError) as e:
            print(f"Skipping module {module.__name__}: {e}")
        for name in dir(module):
            obj = getattr(module, name)
            if inspect.ismodule(obj):
                process_module(obj)

    process_module(autograms)
    return modules


def extract_functions_and_classes():
    """
    Extract the source code of all classes and functions within the `autograms` package.

    Returns:
    - dict: A dictionary mapping the fully-qualified name of each class/function to its source code.
    """
    from autograms import __name__ as root_name
    import autograms

    items = {}

    def process_module(module):
        """
        Process a module to extract classes and functions.
        """
        try:
            module_name = module.__name__
        except AttributeError:
            return  # Some modules might lack a proper __name__

        for name in dir(module):
            obj = getattr(module, name)
            full_name = f"{module_name}.{name}"

            if inspect.isfunction(obj) or inspect.isclass(obj):
                try:
                    # Ensure the object belongs to the autograms package
                    if obj.__module__.startswith(root_name):
                        items[full_name] = inspect.getsource(obj)
                except (TypeError, OSError) as e:
                    print(f"Skipping {full_name}: {e}")

            elif inspect.ismodule(obj) and obj.__name__.startswith(root_name):
                process_module(obj)

    process_module(autograms)
    return items

def extract_docstrings():
    """
    Recursively extract docstrings from all functions and classes in the `autograms` package.
    
    Returns:
    - dict: A dictionary mapping function/class full names to their docstrings.
    """
    processed = set()
    docstrings = {}

    def process_module(module):
        if module in processed or not module.__name__.startswith("autograms"):
            return
        processed.add(module)
        for name in dir(module):
            obj = getattr(module, name)
            if inspect.isfunction(obj) or inspect.isclass(obj):
                full_name = f"{module.__name__}.{name}"
                docstrings[full_name] = inspect.getdoc(obj) or "No docstring available"
            elif inspect.ismodule(obj):
                process_module(obj)

    process_module(autograms)
    return docstrings




docs = extract_docs()
examples = extract_examples()
functions_classes = extract_functions_and_classes()
modules = extract_modules()
docstrings = extract_docstrings()

base_path = "asa_code"
continued_path = "conversation"
final_path = "code_output"


   
common_mistakes_and_tips="""

COMMON MISTAKES AND TIPS (IMPORTANT):


--reply and reply_instruction use a similar mechanism to the input function in python--they send a reply to the user and wait for the user's input. The work similarly to the following code.

```python
#do not use this--it is only to illustrate how reply() works
def simplified_reply(instruction):
    print(instruction)
    user_reply=input("User: ")
    memory_object.add_user_reply(user_reply)

```
```python
#do not use this--it is only to illustrate how reply_instruct() works
def simplified_reply_instruction(instruction):
    reply = thought(instruction)
    print(reply)
    user_reply=input("User: ")
    memory_object.add_user_reply(user_reply)

```
Note that the user_reply will automatically be saved to the memory object when we do this, so future calls to other functions (which also access the memory) will see the user reply. Unlike simplified_reply and simplified_reply_instruction in the hypothetical example above, reply and reply_instruction allow the entire program to return, be serialized and saved, and resumed with the full stack trace and memory recovered. This is accomplished using the autograms function decorator which uses special exceptions to exit the functions and abstract syntax tree manipulation to start the code where it left off when the function is recalled.

Also not that you should NEVER use input() in an autograms function.

--remember that multiple_choice and yes_or_no ask questions directed to the model and not to the user. They are for the model to make decisions, usually based the user's behavior or desired. They should usually be should be asked after a reply() or reply_instruct(). Asking yes_or_no("does the user want x") is meaningless unless it is based on a user response--we won't know the answer magically unless we have also asked the user something similar. Sometimes it may make sense to ask several nested yes or no questions in order to have the model make a more fine grained tree of decisions. So the following is incorrect:

--multiple_choice and yes_or_no are meant to direct the conversation flow depending on what the user appears to want. Each answer should lead to a different follow up. Be sure to be thorough, there may be many possibilities for what a user needs and you want to handle all edge cases.



With multiple_choice(), we always want to consider edge cases of user's who don't fit cleanly into one of the categories we thought of in advance. For instance:
```python
choices = ["user wants x","user wants y","user wants z","None of the above"]
idx = multiple_choice("What does the user want?",choices=choices)

if idx==0:
    #handle user wants x with a reply_instruction() or a call to another @autograms_function() decorated that contains reply_instruction() or other actions
    handle_user_wants_x()
elif idx==1:
     #handle user wants y with a reply_instruction() or a call to another @autograms_function() decorated that contains reply_instruction() or other actions
    handle_user_wants_y()
elif idx==2
     #handle user wants z with a reply_instruction() or a call to another @autograms_function() decorated that contains reply_instruction() or other actions
    handle_user_wants_z()
else:
    #handle user that doesn't fit any of these cases reply_instruction() or a call to another @autograms_function() decorated that contains reply_instruction() or other actions
    handle_edge_case(
```

It is good practice to have the conversation run in an infinite loop at the end so that we can keep replying to the user, for instance

```
@autograms_function()
def chatbot():
    #earlier conversation functions go here
    while True:
        handle_continue_conversation()



@autograms_function()
def handle_continue_conversation():
    #this is very generic,real examples may have more complex behavior
    reply_instruction("Reply to the user")

```




```python
#wrong, don't to this
yes_or_no("Do you want x?")
```
Should instead be this (correct):
```python
reply_instruction("ask the user if they want x")
yes_or_no("does the user want x?)
```

--reply_instruction() is one of the most important functions and it matters to get the instruction argument right. The instruction should be an instruction for how to reply, and not a direct reply. So for instance:


Incorrect:

```python
#wrong, don't do this
reply_instruction("how are you today?")

Correct:

```python
#instead, do this:
reply_instruction("ask the user how they are today")
```

Potentially even better if there is context variable notes_on_user generated from a previous thought() function:

```python
#assuming we have a relevant context string notes_on_user likely generated from the thought() function
reply_instruction(f"Summary of previous interactions: {notes_on_user}\n\nask the user how they are today and ask them about something they previously mentioned")
```


Be careful with import paths. Typical imports for the chatbot code file may look like
```python
from autograms import autograms_function
from autograms.functional import multiple_choice, yes_or_no, reply, reply_instruction, thought, generate_list, extract_code, set_system_prompt
```
with additional imports added as necessary. You should always at the very least import all of the above functions even if you don't use them all since it makes mistakes due to forgotten imports less likely, and makes it easier for the user to add to the code. 

Typical imports for the run file should look like:
```python
from autograms import Autogram
from chatbot_code import [insert name of root function]
```
The chatbot code file will always be called chatbot_code.py and should always be imported from there. 


Also do not use an ADDRESS argument with autograms.functional modules. That is only for autograms.nodes


All autograms.functional and autograms.nodes modules must be called from within functions--they will give an error if you call them outside a function. The reason is because these functions access a special thread specific memory object that is set using a scope. So long as the root function is an @autograms_function(), all functions called from within that will have the appropriate memory scope applied.

"""

@autograms_function()
def chatbot():

    start_prompt = ""

    for doc in docs:
        start_prompt += f"Doc: {doc}\n\n{docs[doc]}"

    for example in examples:
        start_prompt += f"Example: {example}\n\n{examples[example]}"

    start_prompt+="\n\n"+common_mistakes_and_tips+"\n\n"
    start_prompt +="You are Asa (Autograms Seed Agent. You goal is to answer user questions about the docs and help users write code)."
    
    set_system_prompt(start_prompt)
    #import pdb;pdb.set_trace()




    start_message = """Hi! I'm am Asa (Autograms Seed Agent) and I specialize in designing autograms chatbots I'm here to answer any questions you have about autograms and help you get started. Some things I can do are:

--answer any questions you have about autograms
--write an initial draft of autograms code for you and save it in a file 


I am only the first version of myself so I may occasionally make mistakes. In future versions, I will be even better at writing autograms code. 

**It also takes me some time to figure out the answers to questions and/or write code, so it may take me up to 20 seconds to reply.**


So to get started let, me know what you want to know about autograms or what type of chatbot you want to code.
    """


    reply(start_message)

    while True:

        needs_code = yes_or_no("is the user requesting that we write (or revise) code?")

        if not needs_code:
            needs_answer = yes_or_no("is the user asking us a question?")
            if needs_answer: 
                q_idx = multiple_choice("What is the user's question most relevant to?", choices=["autograms","AI and/or programming but not specific no autograms","neither of these"])
                if q_idx==0 or q_idx==1:
                    answer_question()
                else:
                    reply_instruction("tell the user you really only specialize in questions about autograms and writing code but you'll do your best to answer their question. Then follow it up with your best answer.")
            else:
                reply_instruction("reply to the user")

        else:
            needs_chatbot = yes_or_no("is the code the user is asking for a chatbot (or related AI agent application?")
            if needs_chatbot:
                write_code()
            else:
                reply_instruction("reply to the user")



@autograms_function()
def answer_question():
    prompt = "We need to decide how to answer the user's question. We can either answer directly from the docs or take a deeper look at the code. Can we answer the question precisely enough from the docs (given above) or do we need to dig deeper? If it's answerable from the docs, write the answer while brainstorming the reply."

    result = thought(prompt)

    reply_instruction("write the answer as a direct reply to the user.")







            


def get_docstring_list():
    prompt=f"These are the names of all the functions and classes in autograms {docstrings.keys()}. Which class(es) and or function(s) do we want to look up the doc strings for? Specify a list of up to 5 functions. "
    results = generate_list(prompt)

    source=""
    for result in results[:5]:
        if result in functions_classes.keys():
            source+=f"{result}"+"\nsource:\n"+docstrings[result]
        else:

            source+=f"{result}"+"\nsource:\nDoesn't exist, invalid function/class"

    return source
def get_timestamp():
    """
    Generates a timestamp for the current time.

    Returns:
    - str: The current timestamp in 'YYYY-MM-DD-HH:MM:SS' format.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-7]
    timestamp=timestamp.replace(" ","-")
    return timestamp

def get_source_list():
    prompt=f"These are the names of all the functions and classes in autograms {functions_classes.keys()}. Which class(es) and or function(s) do we want to look up the source code for? Specify a list of up to 5 functions. "
    results = generate_list(prompt)

    source=""
    for result in results[:5]:
        if result in functions_classes.keys():
            source+=f"{result}"+"\nsource:\n"+functions_classes[result]
        else:

            source+=f"{result}"+"\nsource:\nDoesn't exist, invalid function/class"

    return source

def get_module_source_list():
    prompt=f"These are the names of all the modules in autograms {modules.keys()}. Which class(es) and or function(s) do we want to look up the source code for? Specify a list of up to 2 modules"
    results = generate_list(prompt)

    source=""
    for result in results[:2]:
        if result in modules.keys():
            source+=f"{result}"+"\nsource:\n"+modules[result]
        else:

            source+=f"{result}"+"\nsource:\nDoesn't exist, invalid function/class"
    return source

@autograms_function()
def write_code():

    
    prompt = "we aren't going to write code just yet--we need to make a plan. Let the user know your plan and ask if it's okay."

    reply_instruction(prompt)


    code_file = "chatbot_code.py"
    run_file = "run_chatbot.py"

    full_file = base_path+"/"+code_file
    full_run_file = base_path+"/"+run_file



    prompt =f"let's write the code. Enclose the code using ```python```. There should be exactly 2 ``python``` blocks. The first one should code the autograms module, which will be saved in {code_file}. The second block should import and call the chatbot by passing the autograms function to an Autogram object"

    
    print("writing code...")
    result = thought(prompt)

    code = extract_code(result,merge_blocks=False)

    if len(code)!=2:
        result = thought(f"There was a problem extracting the last code. let's write the code again. Be sure you close the code using ```python``` or else it won't be extracted correctly. Also make sure there exactly 2 blocks.")
        code = extract_code(result,merge_blocks=False)
        if len(code)==0:
            reply_instruction("let the user know there is a problem saving the code, but respond to them as best as you can.")


    code = fix_problems(code)

    if len(code)!=2:
        result = thought(f"There was a problem extracting the last code. let's write the code again. Be sure you close the code using ```python``` or else it won't be extracted correctly. Also make sure there exactly 2 blocks.")
        code = extract_code(result,merge_blocks=False)
        if len(code)!=2:
            reply_instruction("let the user know there is a problem saving the code, but respond to them as best as you can.")
            return
    
    if not os.path.exists(base_path):
        os.makedirs(base_path)
        print(f"Directory '{base_path}' created successfully.")


    time_base_path = base_path+"/"+get_timestamp()
    os.makedirs(time_base_path)

    
    full_file = time_base_path+"/"+code_file
    full_run_file = time_base_path+"/"+run_file

    with open(full_file,'w') as fid:
        fid.write(code[0])

    with open(full_run_file,'w') as fid:
        fid.write(code[1])
    reply_instruction(f"now we will reply to the user. Let them know you wrote the code directory {time_base_path}. {code_file} contains the code for the chatbot and {run_file} contains the code ro run the chatbot. Tell them to run the code, they can open a new terminal, do `cd {time_base_path}` and `python3 {run_file}`. Also tell them about the code.")

        
@autograms_function()
def fix_problems(code):
    has_problems=yes_or_no(f"Here are some notes about problems to check for:\n{common_mistakes_and_tips} \n\nCheck this code for common problems: {code}\n\nDoes the code contain any of the problems")

    if has_problems:
        new_code = thought(f"this code was flagged for having a problem from this list: {common_mistakes_and_tips}. Rewrite the code and fix any issues that you notice in the above tips.")
        code = extract_code(new_code)
        return code
    else:
        return code
    

@autograms_function(conv_scope="normal")
def general_lookup():
    idx = multiple_choice("What should we lookup to help us get more information?",choices=["function docstrings","function code"])
    if idx == 0:
        result = get_source_list()
    elif idx==1:
        result = get_module_source_list()

    return result



    

    




    











