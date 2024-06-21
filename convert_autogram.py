import json
from autograms import Autogram, AutogramCompiler
from autograms.graph_utils import HTML_TEMPLATE
import pandas as pd
import argparse
import os
import importlib.util
import types


def import_module_by_file(file_path):
    loader = importlib.machinery.SourceFileLoader("__temp__", file_path)
    module = types.ModuleType(loader.name)
    loader.exec_module(module)

    return module.autogram






def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--autogram_file', type=str,help='.py or .csv file with autogram, will support other spreadsheet formats later')
    parser.add_argument('--allow_overwrite', action="store_true",help="allow converted autogram to overwrite even if it alredy exists")
    parser.add_argument('--write_as_pure_python', action="store_true",help="save autogram as pure python instead of compiled from python")
    parser.add_argument('--read_as_pure_python', action="store_true",help="load autogram as pure python instead of compiled from python")
    parser.add_argument('--convert_to', type=str,default=None,help="type to convert to ('py' or 'csv'). By default will be csv if input file is .py and py if input file is .csv")
    args = parser.parse_args()



    
    autogram_file = args.autogram_file

    ind = autogram_file.rfind(".")
    if ind<0:
        raise Exception("invalid autogram file")
    
    path_and_name = autogram_file[:ind]
    ext=autogram_file[ind:]


    
    if ext==".py":
        fid = open(args.autogram_file)
        code=fid.read()

        if args.read_as_pure_python:
            autogram_obj=import_module_by_file(autogram_file)
            autogram=autogram_obj


        else:

            autogram_compiler=AutogramCompiler()

            autogram = autogram_compiler(code,config={})

            autogram.update_autogram()


        if args.convert_to is None:
            args.convert_to="csv"

      
    elif ext==".csv":

                                
        df=pd.read_csv(autogram_file)
        autogram = Autogram(None,None,{},allow_incomplete=True)

        autogram.add_nodes_from_data_frame(df)
        if args.convert_to is None:
            args.convert_to="py"
    else:
        raise Exception("invalid autogram file extension "+ext)


    if args.convert_to=="csv":

        new_df=pd.DataFrame(autogram.convert_to_df())
        fname=path_and_name+".csv"
        if os.path.exists(fname) and not args.allow_overwrite:
            raise Exception(fname +" already exists. use --allow_overwrite to overwrite.")
        else:
            new_df.to_csv(fname,index=False)
    elif args.convert_to=="py":
        if args.write_as_pure_python:
            python_code = autogram.convert_to_pure_python()
        else:
            python_code = autogram.convert_to_hybrid_python()
        fname=path_and_name+".py"


        if os.path.exists(fname) and not args.allow_overwrite:
            raise Exception(fname +" already exists. use --allow_overwrite to overwrite.")
        else:
            fid = open(fname,'w')
            fid.write(python_code)
            fid.close()


    else:
        raise Exception("convertion to " +args.convert_to + " not supported.")


if __name__ == '__main__':
    main()