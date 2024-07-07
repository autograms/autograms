import json
from autograms import read_autogram
from autograms.graph_utils import HTML_TEMPLATE
import pandas as pd
import argparse
import os
import importlib.util
import types
from autograms.graph_utils import visualize_autogram


def import_module_by_file(file_path):


    loader = importlib.machinery.SourceFileLoader("__temp__", file_path)
    module = types.ModuleType(loader.name)
    loader.exec_module(module)

    return module.autogram










def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--autogram_file', type=str,help='.py or .csv file with autogram, will support other spreadsheet formats later')
    parser.add_argument('--filter_category', type=str,default=None,help='only draw graph for states of specific category')
    parser.add_argument('--label_by_inst', action="store_true",help='label graph by instruction instead of node name')
    parser.add_argument('--read_as_pure_python', action="store_true",help="load autogram as pure python instead of compiled from python")
    parser.add_argument('--graph_format',type=str,default="png",help='file format of graph image file (png, pdf, etc.)')
    args = parser.parse_args()


    
    autogram_file = args.autogram_file

    autogram = read_autogram(autogram_file,read_as_pure_python=args.read_as_pure_python,final=False)


    autogram.update(include_inst=args.label_by_inst)

    
    autogram_root_path = os.path.splitext(args.autogram_file)[0]


    visualize_autogram(autogram,root_path=autogram_root_path,filter_category=args.filter_category,graph_format=args.graph_format)



if __name__ == '__main__':
    main()