# AutoGRAMS

[AutoGRAMS](https://github.com/autograms/autograms) (Autonomous Graphical Agent Modeling Software) is a Python library that represents chatbots as stateful, continuously running programs. AutoGRAMS enables you to precisely control the prompts and memory at different points in the conversation. Decisions made during conversations directly influence the program’s execution path, variables persist as the chatbot’s memory, and conversations seamlessly adapt based on the program’s current state.


To get started, you can chat with the **AutoGRAMS Seed Agent** (Asa)--an AutoGRAMS chatbot that runs in the terminal and codes AutoGRAMS chatbots for you 🔥 It can also answer questions about the code it writes or about AutoGRAMS in general. To run **Asa**, follow the **Quick Start** instructions below.


As of the latest version, Autograms can be configured with [Local AI](https://github.com/mudler/LocalAI) and [Huggingface Text Generation](https://github.com/huggingface/text-generation-inference) interface for efficiently running open source LLMs locally, and [Lite LLM](https://github.com/BerriAI/litellm) for connecting to a large set of model APIs. 

The full documentation and tutorials are available in our [web docs](https://autograms.github.io/autograms). 


## Quick start

To talk to the Autograms Seed Agent, which can help you design chatbots and help explain how autograms works, you can use the following steps from a terminal:

Create and activate a fresh conda environment
```
conda create --name test_autograms python=3.9
conda activate  test_autograms
```

Clone repo and install from source
``
git clone https://github.com/autograms/autograms.git
cd autograms
pip install .
```

Set Open AI api key. If you want to use locally running models or other APIs instead, skip ahead to the section on [running other models](running-other-models).

```
export OPENAI_API_KEY=<yourkey>
```

Run the Autograms Seed agent, opens an interactive chatbot in the terminal that can write and save code or answer questions
```
python run_autogram.py
```

Here is a quick video tutorial of these steps [quick video tutorial](https://www.youtube.com/watch?v=MPrpPGqbaOM)

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



If you want to run the latest pushed version and/or make local modifications, you can install autograms with:

```
git clone https://github.com/autograms/autograms.git
cd autograms
pip install .
```

You can install also AutoGRAMS via pip:

```
pip install autograms
```

To visualize AutoGRAMS graphs (optional), install Graphviz. On Linux:

```
sudo apt install graphviz
```

Python >=3.9 is required. If you plan to use OpenAI models or other LLM APIs (see running other models with proxy server), ensure you set up the necessary dependencies and keys.


## Demos and Examples

Explore the `/examples` folder to see sample autograms, including the source code for Asa. Each example demonstrates different capabilities of AutoGRAMS, from simple branching dialogues to complex, stateful agents.

To run a demo, set your open ai api key with 


`export OPENAI_API_KEY=<your key>`

and run:

```
python run_autogram.py --api_key_file  --example_name <example_name>
```

Replace `<example_name>` with the desired example (e.g., `autograms_seed_agent`, `simple_example`, `fraction_tutor`, `general_tutor`, or `recruiter`), or use your own example by manually importing your autograms chatbot in `run_autogram.py`.



You can run Asa (Described above) to help you learn and code autograms with:

```
python run_autogram.py --example_name autograms_seed_agent
```

This will launch an interactive chatbot in the terminal. You can ask the autograms seed agent to design a specific chatbot and it will write and save the code for you. You can also ask it questions about the code it writes or questions about autograms in general. You can try giving it messages like "Code a chatbot that will help me develop a workout plan". It should write and save the code in a new folder and give you instructions on how to run the chatbot it just designed. You can also ask Asa questions about the code it wrote.


To see a more direct application, you can try the recruiter chatbot demo:

```
python run_autogram.py --example_name recruiter
```


If you want to modify an example or create your own in a new file, you can run it from your .py file with:


```
python run_autogram.py --autogram_file path/to/example.py
```

Note that for examples loaded from a file, you must call the root chatbot function 'chatbot' and it must be decorated with `@autograms_function()` like the examples in the repo.

### Open AI token costs

In the above examples, the autograms seed agent agent has long prompts and several model calls, so it uses around around 100k openai input tokens per turn (75%+ of which are usually cached tokens, the cheapest kind), and about 2k output tokens per turn (the most expensive kind). Most of the other examples (like recruiter) have shorter prompts and use far fewer tokens. `run_autogram.py` uses GPT-4o by default. To reduce Open AI api usage cost by a factor of more than 10x, you can run examples with GPT-4o mini using:
```
python run_autogram.py --example_name autograms_seed_agent --model_name gpt-4o-mini
```
although it will sometimes give inferior results. See the [openai documentation](https://openai.com/api/pricing/) for details on their token costs.

The recruiter chatbot and other examples also have much shorter prompts and use fewer tokens.

You can also see the token usage (along with other information about model calls) in the list:

```
python 
memory_object.memory_dict['model_turns']
```


in `run_autogram.py`. This list contains logging information for the whole conversation. Each entry in this list is a dictionary, and entries that have a 'usage_log' field use api model calls and have token use documented.

## Running other models

Autograms can also be run with other models besides openai by setting up proxy servers. Autograms has been tested with:

[Local AI](https://github.com/mudler/LocalAI)--simple CPU or GPU inference with open source models, supports both text generation and embeddings.

[Lite llm](https://github.com/BerriAI/litellm)--Allows other model APIs for text generation and embeddings to be called, and can give more controls over model calls such as rate limits

[Huggingface text generation interface](https://github.com/huggingface/text-generation-inference) -- Professional grade GPU text generation, does not support embeddings



Autograms will most likely work with other openai compatible proxy servers too, so long as structured outputs are handled correctly.


### Quick Example: Running Llama on CPU with Local AI


Local AI is useful if you want to run autograms locally, and supports both text generation and embeddings. It's also feasible to run it completely on the CPU if you don't have access to a GPU. Local AI can be set up with [docker](https://www.docker.com/), or installed from source with instructions on the [Local AI github](https://github.com/mudler/LocalAI).


Note: If you do not have docker installed, are using ubuntu, and want a quick solution, you can run `bash proxy_apis/install_docker.sh` (tested in ubuntu 20.04)

You can run llama with docker : 

docker run -ti --name local-ai -p 8080:8080 localai/localai:latest-cpu run llama-3.2-1b-instruct:q4_k_m

Note that you may need to run docker with `sudo` if this gives a permission error. 

If you would also like to run an embeddings model to work with autograms, you can use:

docker run -ti --name local-ai-embed -p 8081:8080 -v "$(pwd)/proxy_apis:/models" localai/localai:latest-cpu /models/localai_embedding_config.yaml

Note that embeddings aren't necessary for the current examples in the repo, but are needed for autograms that use RAG. We will add some examples of this soon.


You can then open a new terminal window, cd into the autograms repo, and run an example using:

python run_autogram.py --example_name recruiter --model_type proxy --proxy_port 8080 --model_name llama-3.2-1b-instruct:q4_k_m 


Note that compared with openai's best models, the instructions in autograms need slightly more detail for some smaller open source models, otherwise the model can become confused about it's role. /examples/recruiter.py is well optimized for this.

If you have a custom example that needs to use embeddings, assuming you set up both proxies, you can use


python run_autogram.py --autogram_file path/to/file.py --model_type proxy --proxy_port 8080 --model_name llama-3.2-1b-instruct:q4_k_m --embedding_model_name text-embedding-ada-002 --embedding_model_type proxy --embedding_proxy_port 8081


When you want to stop or restart the docker run, you can clean up the previous run with

```
docker stop local-ai
docker rm local-ai

docker stop local-ai-embed
docker rm local-ai-embed
```




### Huggingface TGI


Huggingface TGI allows for professional grade GPU inference of text generation models (but not embeddings models as of now). There are some differences in Huggingface TGI and openai style structured outputs, but we have made an effort to map them in a way that should support most autograms functionality. Huggingface TGI can be run with docker on nvidia GPUs. For CPU only we recommend local AI above.


You can run huggingface TGI on the GPU using docker with with:

`bash proxy_apis/run_huggingface.sh tiiuae/falcon-7b-instruct`

You can change the model and inference settings by changing the shell script.

After your proxy server is running locally, you can open a new window and run:

`python run_autogram.py --example_name recruiter --model_type huggingface_tgi --proxy_port 8080 --model_name tiiuae/falcon-7b-instruct`




### Running Lite LLM

Lite LLM is a proxy that allows you to connect with a wide range of model apis using open-ai-style requests. It can be used to make autograms compatible with many models, so long as structured outputs are correctly supported for that model.

pip install 'litellm[proxy]'


You can then run litellm
litellm --model openai/gpt-4o --port 8080

You can replace openai/gpt-4o with other models. You will need to set your api key in teh environment for the models you want to use. It may not work for APIs that don't have compatible structured outputs. Once the proxy is running, you can open a new terminal, cd into the autograms repo, and run an example with:


python run_autogram.py --example_name recruiter --model_type proxy --proxy_port 8080 --model_name gpt-4o


Be sure to include the model name that matches your lite llm proxy. If you also want to use litellm for embeddings, you can use 
--embedding_model_name [embedding_model]. If the embedding model is on a separate port, you would also need to specify --embedding_proxy_port



## Visualization

AutoGRAMS includes tools to visualize the conversational flow as an interactive graph. For example, you can generate visualizations for the recruiter chatbot with:

```
python visualize_autogram.py --example_name recruiter --save_folder recruiter_graph
```

This will create both a static and interactive graph in the specified folder. You can explore the chatbot flow and decision points by clicking on nodes in the interactive graph.


## Debugging autograms


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
