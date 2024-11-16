# AutoGRAMS

AutoGRAMS (Autonomous Graphical Agent Modeling Software) is a Python library that represents chatbots as stateful, continuously running programs. Unlike traditional chatbots, which often treat conversation turns as isolated events, AutoGRAMS allows agents to function as dynamic programs that retain their full execution state, including variables and control flow, across conversation turns.

By representing a chatbot as a running program, AutoGRAMS enables precise control over dialogue flow. Decisions made during conversations directly influence the program’s execution path, variables persist as the chatbot’s memory, and conversations seamlessly adapt based on the program’s current state.

---

## Key Features

- **Continuously Running Programs**: AutoGRAMS lets you write chatbots as Python programs that maintain their state across interactions. Each user input resumes the program exactly where it left off, enabling highly dynamic, context-aware conversations. 

- **Save and Resume Program State**: Serialize the program’s entire state, including call stack, variables, and control flow. Reload it later to continue the program (and conversation) from its exact state.

- **Dynamic Control Flow**: Use advanced constructs like `GOTO` to move between different parts of your program that represent different states of your chatbot. This allows complex, non-linear dialogue paths that adapt dynamically to user inputs and decisions.

- **LLM-Driven Decisions**: Integrate decision-making powered by LLMs to dynamically guide conversations based on user input, enabling sophisticated branching of the program

- **Memory Management**: AutoGRAMS automatically manages memory, ensuring that variables and conversation history persist across turns.

- **Visualize Conversation Flow**: Compile detailed graphs of your chatbot’s states and logic, helping you design, debug, and understand the flow of conversation at a glance.


AutoGRAMS accomplishes many of these behaviors using a special @autograms_function decorator that enables non-standard python functionality such as saving and loading the state of a program mid-execution and jumping to a predefined location in the code.

The full documentation and tutorials are available in our [web docs](https://autograms.github.io/autograms).

## Installation

You can install AutoGRAMS via pip:

```
pip install autograms
```

If you make local modifications, you can install them with:

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

AutoGRAMS makes it easy to build structured, stateful chatbots. To get started with a recruiter chatbot demo, you can run:

```
python run_autogram.py --api_key_file api_keys.json --example_name recruiter
```

This will launch an interactive chatbot in the terminal, simulating a virtual recruiter.

### API Keys

To use OpenAI or other API-driven models, set your API key as an environment variable:

```
export OPENAI_API_KEY=<your key>
```

Alternatively, you can store your API key in `api_keys.json`. Simply change `"load_from_env"` to `false` and set the `"openai"` key to your API key.

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

Replace `<example_name>` with the desired example (e.g., `simple_example`, `fraction_tutor`, `general_tutor`, or `recruiter`).


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
