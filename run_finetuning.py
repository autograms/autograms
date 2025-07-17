


import json
import os
import argparse
import glob
import dill
import base64


from autograms.finetuning.get_training_messages import get_training_messages,convert_messages,get_training_messages_dpo
from autograms import AutogramConfig

def main():
    # Set up argument parsing for command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, default=None, help='config file')
    parser.add_argument('--model', type=str, default="Qwen/Qwen2.5-32B-Instruct") #huggingface or open ai model
    parser.add_argument('--model_type', type=str, default="huggingface") #can also be openai
    parser.add_argument('--finetuning_type', type=str, default="normal") #or dpo
    parser.add_argument('--tag_query', type=str, default="")
    parser.add_argument('--save_dir', type=str,default = "simulation_data")
    parser.add_argument('--prepare_data_only', action="store_true")
    args = parser.parse_args()



    if args.model_type=='openai':
        if not args.prepare_data_only:

            from autograms.finetuning.openai_finetuning import finetune_openai_jsonl

    elif args.model_type =='huggingface':
        if not args.prepare_data_only:
            if args.finetuning_type=="dpo":
                from autograms.finetuning.huggingface_dpo import dpo_huggingface_jsonl
            elif args.finetuning_type=="normal":
                from autograms.finetuning.huggingface_finetuning import finetune_huggingface_jsonl

    else:
        raise Exception(f"invalid model type {args.model_type}")
    # Load or initialize configuration
    if args.config_file is None:

        autogram_config = AutogramConfig(chatbot_max_input_len=32000)
    else:
        initial_args = {}
        with open(args.config_file) as fid:
            config = json.load(fid)
        # Merge default and loaded config
        config = {**initial_args, **config}
        autogram_config = AutogramConfig(**config)

    memory_list = []

    pkl_files = glob.glob(os.path.join(args.save_dir,"*.pkl"))


    for file in pkl_files:

        with open(file) as fid:
            raw_memory = fid.read()
            recovered_data= base64.b64decode(raw_memory)
            memory_dict = dill.loads(recovered_data)


            memory_list.append(memory_dict)

     
    
    if args.finetuning_type =="dpo":
        train_messages = get_training_messages_dpo(memory_list,autogram_config)


        train_jsonl = os.path.join(args.save_dir,"train_dpo.jsonl")

    else:
        train_messages = get_training_messages(memory_list,autogram_config,tag_query = args.tag_query)
        import pdb;pdb.set_trace()


        train_jsonl = os.path.join(args.save_dir,"train.jsonl")


    use_dpo = args.finetuning_type=="dpo"
    if args.model_type =='openai':
        if not use_dpo:
            convert_messages(train_messages)
        with open(train_jsonl, "w") as file:
            for item in train_messages:
                file.write(json.dumps(item) + "\n")
        if not args.prepare_data_only:
            
            log_message = finetune_openai_jsonl(train_jsonl,model=args.model,use_dpo=use_dpo)
            print(log_message)
    elif args.model_type =='huggingface':
        if not use_dpo:
            convert_messages(train_messages,remove_weight=True)
        with open(train_jsonl, "w") as file:
            for item in train_messages:
                file.write(json.dumps(item) + "\n")

        if not args.prepare_data_only:
            if args.finetuning_type=="dpo":
                log_message = dpo_huggingface_jsonl(train_jsonl,model_name=args.model)
                
            else:
                log_message = finetune_huggingface_jsonl(train_jsonl,model_name=args.model)
                

            print(log_message)


    
    
    

if __name__=="__main__":
    main()


    



