We welcome contributions of agents to AutoGRAMS in the examples folder. If you come up with a useful or illustrative agent chatbot or function, feel free to submit a pull request adding a new sub folder in the /examples folder with your agent. 

The agent can either be a csv agent, a pure python agent, or an autogram compiled from python. Include the appropriate .csv or .py file for the agent in the folder.


Include a file called `run.sh` to run an example of your agent as intended. The agent should be runnable from the root repository directory with:

`bash examples/example_name/run.sh`

`run.sh` should call a the necessary python code with the necessary arguments to run a minimal example of the agent. Also feel free to have `run.sh` point to `run_autograms.py` with the appropriate arguments. The some of the existing examples (recruiter example for instance) should have `run.sh` files that show how to do this.  


Also include a README.md file in your folder. At the minimum, include a description of what the agent does. Feel free to also include a link if you have another repository that also uses the agent.


You can also define any other files needed, potentially including a json config file, in the directory you create for the agent.

