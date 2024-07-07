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