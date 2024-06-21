## Building a simple recruiter chatbot


Let's say we want to build a recruiter chatbot that asks candidates their salary expectations and navigates the conversation to check if these expectations are in line with the range for the position. We want to first ask the user their expecations, and navigate the conversation differently. We also want to be able to handle users that avoid the question.




To get started on coding these, first we set the prompt for the model. The prompt set by a `set_prompt` action wil appear at the start of the prompt indefintely, in contrast to the turn specific instructions which appear at the end of the prompt and usually disappear at the next turn (depending on the configuration settings). We then set a user prompt for simulating the user. This is useful for automatic testing of our agent.

You'll notice in the code and graph, in addition to prompt setting and chat type actions, this agent uses `transition` actions.







<iframe src="../agent_graphs/recruiter_chatbot/full_graph.html" width="100%" height="700px"></iframe>
Simple recruiter chatbot. Click nodes to see fields.