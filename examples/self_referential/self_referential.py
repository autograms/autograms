meta_inst="We need to decide how to deal with the last user reply. Rather than replying directly, write an instruction for another language model to reply. The instruction could be along the lines of 'respond to the user and tell them xyz'"

exec_node(action="chat_exact",name="intro",instruction="Hi there, What can i help you with?")
autogram = self


next_node = exec_node(action="function", name="dynamic_node",transitions=["$next_node"],instruction = "next_node=add_new_node(autogram,meta_inst)")
    
@function
def add_new_node(autogram,meta_inst):

    new_node = check_existing_graph(autogram)

    if len(new_node)>0:
        return new_node

    else:
        

        new_inst=exec_node(action="thought",instruction="$meta_inst")
        new_name=exec_node(action="thought",instruction="We need to come up with a short name for a node that executes this instruction: $new_inst\nThe name must be all lower case letters and underscore ('_'). Reply with the name only with no spaces")
        
        while not(meta_utils.check_node_name(new_name)):
            new_name=exec_node(action="thought",instruction="We need to come up with a short name for a node that executes this instruction: $new_inst\nThe name must be all lower case letters and underscore ('_'). The last name was invalid, please be sure to reply with the name only and obey the rules about characters.")
        
        autogram.add_node(action="chat",instruction=new_inst,name=new_name,transitions=["dynamic_node"])
    return new_name

#TODO: implement function that decides whether to return an existing node the graph or make a new one.
@function
def check_existing_graph(autogram):

    empty=""
    return empty
