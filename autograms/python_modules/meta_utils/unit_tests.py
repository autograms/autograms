from autograms import AutogramConfig, AutogramCompiler
import json

API_KEY_FILE="api_keys.json"


config = AutogramConfig(include_default_python_modules=True)

fid = open(API_KEY_FILE)
api_keys=json.load(fid)

autogram_compiler=AutogramCompiler()




code = """
def check_name(node_name):

    result = meta_utils.check_node_name(node_name)

    return result
"""


autogram = autogram_compiler(code,config)

autogram.update_api_keys(api_keys)
autogram.allow_incomplete=False
autogram.update_autogram()


#an invalid name
function_args = ["my_node#@e"]


result = autogram.apply_fn("check_name()",function_args)

#should be false
print(result)