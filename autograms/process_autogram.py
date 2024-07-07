import os
import importlib.util
import types
import pandas as pd
import json
from autograms import Autogram, AutogramConfig, AutogramCompiler

def import_module_by_file(file_path):


    loader = importlib.machinery.SourceFileLoader("__temp__", file_path)
    module = types.ModuleType(loader.name)
    loader.exec_module(module)

    return module.autogram


def read_autogram(autogram_file,read_as_pure_python=False,autogram_config=None,api_keys={},final=True):
    """
    read an autogram from a .py or .csv file
    arguments:

    autogram_file - path to .py or .csv file with autogram
    read_as_pure_python - if autogram_file is .py, read as pure python as opposed to autogram compiled from python.
    autogram_config - object of AutogramConfig type to initialize autogram with
    api_keys - dictionary api key environment variables (if api_keys["load_from_env"]==True) or direct api keys otherwise
    final - should we check autogram for errors/undefined transitions. Set this to false when plotting graphs of autograms we are in the process of coding

    """
    ext = os.path.splitext(autogram_file)[1]


    if ext==".py":
        fid = open(autogram_file)
        code=fid.read()

        if read_as_pure_python:
            autogram_obj=import_module_by_file(autogram_file)
            autogram=autogram_obj


        else:

            autogram_compiler=AutogramCompiler()
            if autogram_config is None:
                autogram_config=AutogramConfig()

            autogram = autogram_compiler(code,config=autogram_config)

            if not api_keys=={}:
                autogram.update_api_keys(api_keys)
            
            autogram.update(finalize=final)


      
    elif ext==".csv":

                                
        df=pd.read_csv(autogram_file)
        autogram = Autogram(autogram_config,None,api_keys =api_keys,allow_incomplete=True)

        autogram.add_nodes_from_data_frame(df)
 
        autogram.update(finalize=final)
        
    else:
        raise Exception("invalid autogram file extension "+ext)
    
    return autogram


def write_autogram(autogram,fname,write_as_pure_python=True,allow_overwrite=False):

    """
    write an autogram as .py or .csv file
    arguments:

    autogram - an object of type Autogram
    write_as_pure_python - if autogram_file is .py, write as pure python as opposed to autogram compiled from python.
    allow_overwrite - overwrite file if it already exists

    """


    new_ext = os.path.splitext(fname)[1]



    if new_ext==".csv":

        new_df=pd.DataFrame(autogram.convert_to_df())

        if os.path.exists(fname) and not allow_overwrite:
            raise Exception(fname +" already exists. use allow_overwrite to overwrite.")
        else:
            new_df.to_csv(fname,index=False)
    elif new_ext==".py":
        if write_as_pure_python:
            python_code = autogram.convert_to_pure_python()
        else:
            python_code = autogram.convert_to_hybrid_python()
        


        if os.path.exists(fname) and not allow_overwrite:
            raise Exception(fname +" already exists. use allow_overwrite to overwrite.")
        else:
            fid = open(fname,'w')
            fid.write(python_code)
            fid.close()


    else:
        raise Exception("conversion to " +new_ext + " not supported.")