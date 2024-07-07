
from autograms import read_autogram, write_autogram 
import argparse
import os



def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--autogram_file', type=str,help='.py or .csv file with autogram, will support other spreadsheet formats later')
    parser.add_argument('--allow_overwrite', action="store_true",help="allow converted autogram to overwrite even if it alredy exists")
    parser.add_argument('--write_as_pure_python', action="store_true",help="save autogram as pure python instead of compiled from python")
    parser.add_argument('--read_as_pure_python', action="store_true",help="load autogram as pure python instead of compiled from python")
    parser.add_argument('--convert_to', type=str,default=None,help="type to convert to ('.py' or '.csv'). By default will be .csv if input file is .py and .py if input file is .csv")
    args = parser.parse_args()

    
    autogram_file = args.autogram_file

    autogram = read_autogram(autogram_file)

    ext = os.path.splitext(autogram_file)[1]
    root_path = os.path.splitext(autogram_file)[0]



    if ext==".py":


        if args.convert_to is None:
            args.convert_to=".csv"

      
    elif ext==".csv":


        if args.convert_to is None:
            args.convert_to=".py"


    new_file = root_path+args.convert_to
    write_autogram(autogram,new_file,write_as_pure_python=args.write_as_pure_python)



if __name__ == '__main__':
    main()