from autograms import read_autogram
import argparse
import json


LIST_TO_SORT=[6,5,-6,1,14,2000,3,2,100]

def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--autogram_file', type=str,help='csv or py file with agent')
    parser.add_argument('--api_key_file', type=str)
    args = parser.parse_args()



    with open(args.api_key_file) as f:
        api_keys = json.load(f)


    autogram=read_autogram(args.autogram_file,api_keys=api_keys)

    function_args = [LIST_TO_SORT]

    result = autogram.apply_fn("merge_sort()",function_args)

    print("unsorted list: "+ str(LIST_TO_SORT))
    print("sorted list: "+ str(result))



if __name__ == '__main__':
    main()
