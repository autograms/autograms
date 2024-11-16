import os

# Get the current directory of the Python script
current_directory = os.path.dirname(__file__)
from .graph import compile_graph
# Construct the relative path to the file
file_path = os.path.join(current_directory, 'template.html')
# Read the HTML template file
with open(file_path, 'r') as file:
    HTML_TEMPLATE = file.read()