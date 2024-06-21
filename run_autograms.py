
import random

import pandas as pd

import json

from autograms import Autogram, MemoryObject, AutogramConfig, AutogramCompiler

import argparse
import importlib.util
import types




def import_module_by_file(file_path):
    loader = importlib.machinery.SourceFileLoader("__temp__", file_path)
    module = types.ModuleType(loader.name)
    loader.exec_module(module)

    return module.autogram



def simulate_nodes(autogram,interactive=False,user_id='123',max_turns=10,memory_object=None,force_start=None,test_mode=False):
    
    user_response=""
    
    for i in range(max_turns):

        response,memory_object = autogram.reply(user_response,memory_object=memory_object,set_state=force_start,test_mode=test_mode)
        force_start=None

        print("Chatbot: " + response)
        if i<max_turns:
            if interactive:
                user_response=input("User: ")
            else:
                
                user_response,sampled_state,success = autogram.simulate_user(memory_object=memory_object,test_mode=test_mode)
                print("User: " + user_response)

                if user_response =="<end>":
                    break


    return memory_object






def get_conv_turns(memory_dict):



    out_strs=[]

    for turn in memory_dict['model_turns']:
        outstr=""
        if turn["model"]=="chatbot":
            outstr = "state: "+ turn["state"]+"\n"
            input_str = ""
            for i in range(len(turn["input_history"])):
                if i>0:
                    input_str+=turn["output_history"][i-1]+"\n"
                input_str+=turn["input_history"][i]+"\n"
            

            outstr+=input_str+'\n'
            outstr+="response: "+ turn["model_response"]
        else:
            outstr = "state: "+ turn["state"]+"\n"
            input_str = turn["input_text"]


            outstr+=input_str+'\n'
            outstr+="response: "+ str(turn["class_pred"])


        out_strs.append(outstr)
    return out_strs




def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--autogram_file', type=str,help='.csv or .py file with autogram,')
    parser.add_argument('--api_key_file', type=str,help='json file with api keys.',default=None)
    parser.add_argument('--config_file', type=str,help='json file with fields for autogram config',default=None)
    parser.add_argument('--user_id', type=str,default="123",help='id number for autogram and output file')
    parser.add_argument('--interactive', action="store_true",help='run user interactive autogram instead of simulation')
    parser.add_argument('--read_as_pure_python', action="store_true",help="load autogram as pure python instead of compiled from python")
    parser.add_argument('--load_from_save', action="store_true",help='load memory dict from previous conversation')
    parser.add_argument('--self_referential', action="store_true",help="allow references to autogram's own object, overwritten by field in config field if provided")
    parser.add_argument('--include_python_modules', action="store_true",help="include all autograms python modules, overwritten by field in config file it provided")
    parser.add_argument('--save', action="store_true",help='save memory dict so conversation can be reloaded later')
    parser.add_argument('--include_test', action="store_true",help='Test spreadsheet to see if errors result, reccomended for first run after saving spreadsheet.')
    args = parser.parse_args()




    
    autogram_file = args.autogram_file
    load_from_save=args.load_from_save
    save=args.save
    interactive = args.interactive

    user_id = args.user_id


    if not args.api_key_file is None:
        fid = open(args.api_key_file)
        api_keys = json.load(fid)
        
    else:
        api_keys=dict()

        

    ind = autogram_file.rfind(".")
    if ind<0:
        raise Exception("invalid autogram file")
    
    path_and_name = autogram_file[:ind]
    ext=autogram_file[ind:]

    if args.config_file is None:


        autogram_config=AutogramConfig(self_referential=args.self_referential,include_default_python_modules=args.include_python_modules)
    else:


        initial_args = {"self_referential":args.self_referential,"include_default_python_modules":args.include_python_modules}
        with open(args.config_file) as fid:
            config = json.load(fid)

        config={**initial_args, **config }

        autogram_config=AutogramConfig(**config)
        
        


  
    if ext==".py":
        fid = open(args.autogram_file)
        code=fid.read()

        if args.read_as_pure_python:
            autogram=import_module_by_file(autogram_file)


        else:

            autogram_compiler=AutogramCompiler()
            autogram = autogram_compiler(code,config=autogram_config)
            autogram.update_api_keys(api_keys)

            autogram.allow_incomplete=False
            autogram.update_autogram()


      
    elif ext==".csv":

                                
        df=pd.read_csv(autogram_file)
        autogram = Autogram(autogram_config,df,api_keys)


    else:
        raise Exception("invalid autogram file extension "+ext)





    if args.include_test:

        for i in range(0,10):
            memory_dict=simulate_nodes(autogram,user_id=user_id,test_mode=True,max_turns=20)
            


    for i in range(0,1):

        if load_from_save:

            fid = open("simulated_user_" + str(user_id) +".json",'r')
            memory_object= json.load(fid)
            fid.close() 

        else:
            memory_object=simulate_nodes(autogram,interactive=interactive,user_id=user_id)
            if save:
                fid = open("simulated_user_" + str(user_id) +  ".json",'w')
                json.dump(memory_dict,fid)
                fid.close()

        out_strs=get_conv_turns(memory_object.memory_dict)




        
    import pdb;pdb.set_trace()







if __name__ == '__main__':
    main()
