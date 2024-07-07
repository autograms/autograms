


def design_chatbot(prompt):
    exec_node(
        action="set_prompt",
        instruction="Your goal is to write chatbots in a new language/framework that is very similar to python. Everything will be explained to you in steps."
    )




    autogram = MetaDesignedAutogram()



    outline_prompt="I want to model a conversational agent based on this information:\n\n"+prompt+"\n\nWrite down a list of the steps of things the recruiter needs to task or tell the user. Incorporate this into a detailed outline of the different ways the conversation may go. Include a numbered list and bullet points describing ways the conversation may vary."

    graph_prompt="based on this outline, i want to represent the ways the conversation could go graphically. let's make a graphviz graph using the dot language to represent the conversation. I want each node in the graph to represent 1 turn from the agent, and i want each edge to represent 1 possible way a user might reply. Be sure to label all nodes and edges. I need each node labeled by  a short description of how the agent will reply, and each edge should be labeled by a short description of the user's reply that leads to that transition. Don't worry about styling or explaining the graph for now. Be sure to enclose the graph code using ```dot```."


    outline= exec_node(action="thought",instruction="$outline_prompt")


    graph_reply_orig= exec_node(action="thought",instruction="$graph_prompt")

    graph_code= autogram.extract_code(graph_reply_orig)


    graph_problems = autogram.check_graph(graph_code)

    if len(graph_problems)>0:
         
        new_graph_prompt="Remember, each node should labeled by a short description of how the agent will reply, and each edge should be labeled by a short description of the user's reply that leads to that transition. The graph had the following issues: "+graph_problems


        graph_reply= exec_node(action="thought",instruction="$new_graph_prompt")

        graph_code= autogram.extract_code(graph_reply)

    graph_nodes = autogram.extract_nodes_and_edges(graph_code)


    design_autogram_from_graph(graph_nodes,outline,autogram)

    autogram.add_node(
        action="chat",
        name="terminal",
        instruction="Reply to the user",
        transitions = ["terminal"]
    )


    return autogram

    


def design_autogram_from_graph(graph_nodes,outline,autogram):

    
    for node in graph_nodes:


        design_node(node,outline,autogram)


def design_node(node,outline,autogram):

    next_prompt = "We are trying to design a chatbot. This is an outline of the ways we want the chatbot agent to react in different conversational scenarios:\n\n"+outline+"\n\nWe need to design a node of the chatbot. We are currently focusing on the node: "+node["name"]
    if "p_transitions" in node and len(node["p_transitions"])>0:
        if len(node["p_transitions"])>1:

            next_prompt =next_prompt + "\nThis node will follow a user reply described by one of the following scenarios:\n\n--"+ "\n\n--".join(node['p_transition_scenarios'])
        else: 
            next_prompt =next_prompt + "\nThis node will follow a user reply described the following scenario:\n\n"+['p_transition_scenarions'][0]

    next_prompt += "\n\nThe goal for this node is for the agent to go along with the following scenario: "+ node["scenario"]
    next_prompt += "\n\nWrite an prompt for the agent so that it will follow this scenario. Remember a prompt is an instruction for the model, not an actual reply. Some examples that are bad prompts are:\nHi, It's great to meet you, my name is Alex!\nDo you have any questions about this math problem?\nCan you tell me about your day?\nSome good examples of prompts are:\nIntroduce yourself to the user as Alex.\nAsk the user if they have any questions about the math problem.\nAsk the user how their day is going.\nWrite a prompt for the scenario: "+ node["scenario"] + ". Reply with the prompt and nothing else."
    
    instruction = exec_node(action="thought",instruction="$next_prompt")

    if len(node["transitions"])>0:


        if len(node["transitions"])==1:
            autogram.add_node(action="chat",name=node["name"],instruction=instruction,transitions = node["transitions"])

        else:
            next_prompt = "We need to be able to distinguish between several possible user replies using a multiple choice question we will write. The agents last reply was decribed by: \n\n"+ node["scenario"]+"\n\nThe user is expected to reply in one of "+str(len(node["transitions"])) +" possible ways as follows:\n"

            option_list=""
            for iter in range(len(node["transitions"])):

                option_list =option_list + str(iter+1)+". " + node['transition_scenarios'][iter]+"\n\n"

            next_prompt = next_prompt+option_list

            if len(node["transitions"])==2:

                next_prompt =next_prompt+"We need to decide the question and choices, where question will be a string and choices will be a list. The question isn't being asked directly of the user, but is being applied to the user's reply. This question will be sent to a predictor model that will predict the answer from the user's response. We will make a json string to do this. Some common examples might be mulitple_choice(question=\"Did the user predict the answer correctly\",choices=[\"no\",\"yes\"]). means that \"no\" would apply to the first possible user reply, and \"yes\" would apply to the possible second user reply. Make sure the order of choices corresponds to the order of user replies. As a reminder, the user reply possibilities we need this to apply to are as follows:\n"+option_list+ "\nFormat your answer as a single python statement calling multiple_choice(question=\"write the question\",answer=[\"answer choice1\",\"answer_choice2\"]) replacing the string fields with the actual question and answers."

            
            else:


                next_prompt = next_prompt+"We need to decide the question and choices, where question will be a string and choices will be a list. The question isn't being asked directly of the user, but is being applied to the user's reply. This question will be sent to a predictor model that will predict the answer from the user's response. We will make a python function call called multiple_choice() to do this. Some common examples might be mulitple_choice(question=\"Which of the following is true about the user's reply?\",choices=[\"the user replied with a correct answer.\",\"The user replied with an incorrect answer.\", \"The user asked a question\"]). This means that \"the user replied with a correct answer.\" would apply to the first possible user reply, \"The user replied with an incorrect answer.\" would apply to the second user reply, and \"The user asked a question\" would apply to the third possible user replies. Make sure the length of the choices matches the number of possible user replies. Also be sure the order of choices corresponds to the order of user replies. As a reminder, the user reply possibilities we need this to apply to are as follows:\n"+option_list+ "\nFormat your answer as a single python statement calling multiple_choice(question=\"write the question\",answer=[\"answer choice1\",\"answer_choice2\",...]) replacing the string fields with the actual question and answers."

             

            transition_args_jsons = exec_node(action="thought",instruction="$next_prompt")

            transition_args = autogram.parse_transition_args(transition_args_jsons)

            if not(len(transition_args["choices"])==len(node["transitions"])):
                #pause program to debug if something goes wrong
                debug_checkpoint()

            autogram.add_node(action="chat",name=node["name"],instruction=instruction,transitions = node["transitions"], transition_question=transition_args["question"],transition_choices=transition_args["choices"])


    else:
        autogram.add_node(action="chat",name=node["name"],instruction=instruction,transitions = ["terminal"])
















    




        

        

        


