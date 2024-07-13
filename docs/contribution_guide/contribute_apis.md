### Contributing python modules and APIs

We welcome contributions to python modules in AutoGRAMS that are useful for AI agents to call in 'python_function' nodes. Some useful APIs could be APIs that search the web for text or images, APIs that perform actions like send emails, or any python function that would be helpful for an agent to be able to call. 


A python modules are stored in the `autograms/python_modules` directory. Each module gets it's own directory. The directory for the model must have an `__init__.py` file, a `unit_test.py` file, and  python file(s) that contain the callable functions in the module. The `__init__.py` file should import the callable functions for that module. For instance the `openai_utils` module init file (which as of the time of writing of this doc, is only set up for images, but will later contain more) contains the following code:

```
from .generate_image import generate_image

api_key_name="openai"

api_key=None
```

Modules that do not need api keys do not need the `api_key_name` or `api_key` attribute to be defined. `api_key` is a placeholder for an api key to be added to the module later, which happens in `autograms/statement_interpreter.py`. All autograms accept a dictionary of api keys, which is usually loaded from `api_keys.json`. By default, the statement interpreter expects api key names to match the module names. However, if they do not match, it is still possible for the statement interpreter to find them if the `api_key_name` atrribute is defined in the `__init__.py` file. In the above example, we want to reuse the `openai` api key (also used by chatbot and classifier) to our module called `openai_utils`. Setting `api_key_name="openai"` in the `__init__.py` of openai_utils ensures that the api key will still be matched if it is called "openai" in `api_keys.json`.

When referencing the api key from within the module, it must be imported inside a function. For instance, the generate_image function in openai_utils includes the statement `from . import api_key`. By the time the function is called, the api key will have been set by the statement interpreter.
```
def generate_image(prompt,model="dall-e-3",size="1024x1024"):

    
    from openai import OpenAI

    from . import api_key
    client =  OpenAI(api_key=api_key)

    
    image = client.images.generate(
    model=model,
    prompt=prompt,
    n=1,
    size=size
    )
    return image.data[0]
```

In order to test functions in the callable modules you define, include a file called unit_test.py in the module directory. The unit test code for the openai_utils module could serve as a template and is given below:

```
from autograms import AutogramConfig, AutogramCompiler
import json

API_KEY_FILE="api_keys.json"

config = AutogramConfig(include_default_python_modules=True)

fid = open(API_KEY_FILE)
api_keys=json.load(fid)
autogram_compiler=AutogramCompiler()


code = """
def get_image(prompt):

    image = openai_utils.generate_image(prompt)

    return image
"""


autogram = autogram_compiler(code,config)
autogram.update_api_keys(api_keys)
autogram.allow_incomplete=False
autogram.update_autogram()


function_args = ["An image of a beach with large waves."]
result = autogram.apply_fn("get_image()",function_args)
print(result.url)
```

In the above example, a block of code (in AutoGRAMS compiled from python) is defined to wrap the function in the module, and the code is tested using the `autogram.apply_fn()` method. For modules with multiple functions, define each of the functions in the code block and test them seperately one by one with autogram.apply_fn() statements for each function.

We welcome pull requests that define new modules, or add new functions to existing modules, provided the pull request also includes the appropriate additions to the unit tests and init files.



