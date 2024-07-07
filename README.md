
# AutoGRAMS


AutoGRAMS (Autonomous Graphical Agent Modeling Software) is a framework and high level programming language for designing AI agents and chatbots using a combination of graphical and programming elements.

The full documentation and tutorials are available in our [web docs](https://github.autograms.io). 

AutoGRAMS can be installed with:

`pip install autograms` 

If you make local modifications, you can install them with `pip install .` from the root directory of your copy of the [github repository](https://github.com/autograms/autograms)

To be able visualize AutoGRAMS graphs, install graphviz, which can be done in linux with:

`sudo apt install graphviz`

Python >=3.9 is needed. You will also need to install pytorch for huggingface language models.


## Getting Started Demo

To use openai language models, the fastest way to start is to set the api key in the in the environment, which can be done in linux with:
`export OPENAI_API_KEY=<your key>` 

If you'd prefer to store your api key in a file, you can open `api_keys.json`, change "load_from_env" to `false`, and set the value of "openai" to be equal to your api key. 


To get started with a recruiter agent demo, run `bash examples/recruiter/run.sh`


Running this will trigger an interactive chatbot in the terminal with an ai recruiter agent



## Visualization
Autograms can be visualized with `make_interactive_graph.py`, with no api key required.

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
See /examples folder for example autograms .csv and .py programs. Also see the /tutorial_examples folder for tutorials covered in the web documentation.


You can also run any of the examples in the example folder from the root repository directory with: 

`bash examples/example_name/run.sh`



