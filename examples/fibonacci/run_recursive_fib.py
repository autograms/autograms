from autograms import read_autogram
import argparse
import json


INTEGER=7

def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--autogram_file', type=str,help='csv or py file with agent')
    parser.add_argument('--api_key_file', type=str)
    args = parser.parse_args()



    with open(args.api_key_file) as f:
        api_keys = json.load(f)


    autogram=read_autogram(args.autogram_file,api_keys=api_keys)

    function_args = [INTEGER]

    result = autogram.apply_fn("fibonacci()",function_args)

    print("Fibonacci(" + str(INTEGER) + ") = " + str(result))




if __name__ == '__main__':
    main()
