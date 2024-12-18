# AutoGRAMS

[AutoGRAMS](https://github.com/autograms/autograms) (Autonomous Graphical Agent Modeling Software) is a Python library that represents chatbots as stateful, continuously running programs. Unlike traditional chatbots, which often treat conversation turns as isolated events, AutoGRAMS allows agents to function as dynamic programs that retain their full execution state, including variables and control flow, across conversation turns.

By representing a chatbot as a continuously running program, AutoGRAMS enables you to precisely control the prompts and memory at different points in the conversation. Decisions made during conversations directly influence the program’s execution path, variables persist as the chatbot’s memory, and conversations seamlessly adapt based on the program’s current state.


To get started, you can chat with the AutoGRAMS Seed Agent (Asa)--an AutoGRAMS chatbot that runs in the terminal and helps you code autograms. See instructions for running this below.


The full documentation and tutorials are available in our [web docs](https://autograms.github.io/autograms). 


We also invite you to join the [AutoGRAMS community on discord](https://discord.gg/7U3pP75C) with over 40 members to learn more and get support with building chatbots.



---

## Key Features

- **Continuously Running Programs**: AutoGRAMS lets you write chatbots as Python programs that maintain their state across interactions. Each user input resumes the program exactly where it left off, enabling highly dynamic, context-aware conversations. 

- **Save and Resume Program State**: Serialize the program’s entire state, including call stack, variables, and control flow. Reload it later to continue the program (and conversation) from its exact state.

- **Dynamic Control Flow**: Use advanced constructs like `GOTO` to move between different parts of your program that represent different states of your chatbot. This allows complex, non-linear dialogue paths that adapt dynamically to user inputs and decisions.

- **LLM-Driven Decisions**: Integrate decision-making powered by LLMs to dynamically guide conversations based on user input, enabling sophisticated branching of the program

- **Memory Management**: AutoGRAMS automatically manages memory, ensuring that variables and conversation history persist across turns.

- **Visualize Conversation Flow**: Compile detailed graphs of your chatbot’s states and logic, helping you design, debug, and understand the flow of conversation at a glance.


AutoGRAMS accomplishes many of these behaviors using a special @autograms_function() decorator that enables non-standard python functionality such as saving and loading the state of a program mid-execution and jumping to a predefined location in the code. 



## Installation

You can install AutoGRAMS via pip:

```
pip install autograms
```

If you want to make local modifications you can install with:

```
git clone https://github.com/autograms/autograms.git
cd autograms
pip install .
```

To visualize AutoGRAMS graphs, install Graphviz. On Linux:

```
sudo apt install graphviz
```

Python >=3.9 is required. If you plan to use OpenAI models or other LLM APIs, ensure you set up the necessary dependencies and keys.

## Getting Started

AutoGRAMS makes it easy to build structured, stateful chatbots. We have an autograms chatbot in this repository that can help you code other autograms chatbots.  



To start, you can set your api key with:


`export OPENAI_API_KEY=<your key>`

Then you can run an autograms chatbot that will help you learn and code autograms with:

```
python run_autogram.py --example_name autograms_seed_agent
```

This will launch an interactive chatbot in the terminal. You can ask the autograms seed agent to design a specific chatbot and it will write and save the code for you. You can also ask it questions about the code it writes or questions about autograms in general.


To see a more direct application, you can try the recruiter chatbot demo:

```
python run_autogram.py --example_name recruiter
```

### Open AI token costs

In the above examples, the autograms seed agent agent has long prompts and several model calls, so it uses around around 100k openai input tokens per turn (75%+ of which are usually cached tokens, the cheapest kind), and about 2k output tokens per turn (the most expensive kind). Most of the other examples (like recruiter) have shorter prompts and use far fewer tokens. `run_autogram.py` uses GPT-4o by default. To reduce Open AI api usage cost by a factor of more than 10x, you can run examples with GPT-4o mini using:
```
python run_autogram.py --example_name autograms_seed_agent --model_name gpt-4o-mini
```
although it will sometimes give inferior results. See the [openai documentation](https://openai.com/api/pricing/) for details on their token costs.

You can also see the token usage (along with other information about model calls) in the list:

```
python 
memory_object.memory_dict['model_turns']
```
in `run_autogram.py`. This list contains logging information for the whole conversation. Each entry in this list is a dictionary, and entries that have a 'usage_log' field use api model calls and have token use documented.



## Visualization

AutoGRAMS includes tools to visualize the conversational flow as an interactive graph. For example, you can generate visualizations for the recruiter chatbot with:

```
python visualize_autogram.py --example_name recruiter --save_folder recruiter_graph
```

This will create both a static and interactive graph in the specified folder. You can explore the chatbot flow and decision points by clicking on nodes in the interactive graph.


## Demos and Examples

Explore the `/examples` folder for more sample autograms. Each example demonstrates different capabilities of AutoGRAMS, from simple branching dialogues to complex, stateful agents.

To run a demo:

```
python run_autogram.py --api_key_file api_keys.json --example_name <example_name>
```

Replace `<example_name>` with the desired example (e.g., `autograms_seed_agent`, `simple_example`, `fraction_tutor`, `general_tutor`, or `recruiter`), or use your own example by manually importing your autograms chatbot in `run_autogram.py`.

## debugging autograms


`python debug_autogram.py --example_name <example_name>`

Can be used to quickly simulate random conversation trajectories with dummy users with dummy model calls (no api usage so long as all api calls are within autograms) and this is useful for detecting bugs that may not occur often. You can also debug your own example by manually importing your autograms chatbot in `debug_autogram.py`.

## Citing AutoGRAMS

If you use this work in research, please cite the following paper:

```
@article{krause2024autograms,
  title={AutoGRAMS: Autonomous Graphical Agent Modeling Software},
  author={Krause, Ben and Chen, Lucia and Kahembwe, Emmanuel},
  journal={arXiv preprint arXiv:2407.10049},
  year={2024}
}
```
