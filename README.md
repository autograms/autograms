
# AutoGRAMS


AutoGRAMS (Autonomous Graphical Agent Modeling Software) is a framework and high level programming language for designing AI agents and chatbots using a combination of graphical and programming elements.

AutoGRAMS can be installed with:

`pip install .` from the root directory of the cloned [github repository](https://github.com/autograms/autograms)

to visualize graphs, install graphviz with:

`sudo apt install graphviz`

Python >=3.9 is needed. You will also need to install pytorch for huggingface language models.


## Getting Started Demo

Make sure to substitute put the api keys in an api_keys.json file if using the openai api. json text should be of the format`{"openai","sk-xxxxxxxx"}`. 

To get started with a recruiter agent demo, run `python run_autograms.py --autogram_file examples/recruiter/recruiter_agent_with_email.csv --api_key_file api_keys.json`



Running this will trigger a simulation where the language model also replies as the user. To interact with the language model yourself, you can use the `--interactive` flag
## Visualization
Autograms can be visualized with `make_interactive_graph.py, with no api key required.

For example:
`python make_interactive_graph.py --autogram_file examples/recruiter/recruiter_agent_with_email.csv`
creates an interactive html graph.
In this example it is saved to `/examples/recruiter/recruiter_agent_with_email/full_graph.html`.

Additional information may be viewable by clicking on nodes in the interactive graph. This information may include the action, instruction, and/or transition question.

## Utilities
It is possible to convert back and forth between python and csv autograms using `convert_autogram.py`.

For example:
`python convert_autogram.py --autogram_file examples/recruiter/recruiter_agent_with_email.csv`
will save a .py file by the same name in the same directory.
The .py files created by `convert_autogram.py` can be used inplace of a .csv file when running most scripts

## Demos
See /examples folder for example autograms .csv and .py programs. Also see the /tutorial_examples folder for tutorials covered in the web documentation

Advanced -- Try out a simple chatbot that uses a proof-of-concept self-referential autogram that can manipulate its own object. This example also uses AutoGRAMS compiled from python-like syntax.
`python run_autograms.py --api_key_file api_keys.json --autogram_file examples/self_referential/self_referential.py --self_referential --include_python_modules --interactive`