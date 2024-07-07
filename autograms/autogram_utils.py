
import time
import random
import numpy as np
import ast
import operator






def longest_common_substring(string1, string2):
    answer = ""
    len1, len2 = len(string1), len(string2)
    for i in range(len1):
        for j in range(len2):
            lcs_temp = 0
            match = ''
            while ((i+lcs_temp < len1) and (j+lcs_temp<len2) and string1[i+lcs_temp] == string2[j+lcs_temp]):
                match += string2[j+lcs_temp]
                lcs_temp += 1
            if len(match) > len(answer):
                answer = match
    return answer

def post_process_user_responses(responses):


    for j in range(len(responses)):
        response = responses[j].replace("**","")
        ind_nn = response.find("\n\n")
        if ind_nn>5:
            print("Shortening potential multi user response")
            response = response[:ind_nn]

        if ":" in response[:20]:
            ind = response.find(":")
            response = response[ind+1:]
            if response[0]==" ":
                response = response[1:]
        responses[j]=response
    return responses[0]

def post_process_responses(responses,required_suffix="",banned_phrases=[], required_len=0):
    """
    Post processing responses. 
    Checks to see if response meets requirements.
    Also finishes completion for responses with required suffix.
    Removes some common mistakes from model, such as:
        re-including '**' from promt when using required suffix
        including extra text like "Here is the reply:" at start of reply
    """
    for j in range(len(responses)):

        if len(required_suffix)>0:
            response = responses[j].replace("**","")
        else:
            response=responses[j]

        if ":" in response[:80]:
            ind = response.find(":")
            response = response[ind+1:]
            if response[0]==" ":
                response = response[1:]
        responses[j]=response

    best_responses=[]
    for response in responses:


        if len(required_suffix)>0:
            response,req_satisfied = proc_response(response,required_suffix)
        else: 
            req_satisfied = True

        if req_satisfied:
            if len(banned_phrases)>0:
                for phr in banned_phrases:
                    if phr.lower() in response.lower():
                        req_satisfied=False

        if req_satisfied:
            if len(response)<required_len:
                req_satisfied=False

        if req_satisfied:
            best_responses.append(response)

    passed=True
    if len(best_responses)>=1:
        response = best_responses[0]

    else:

        if len(required_suffix)>0:
            response=required_suffix
        else:
            response = responses[0]
            passed=False

    return response,passed
def proc_response(response,required_text,min_overlap_req=40):


    if not(required_text is None):
        

        overlap_req = longest_common_substring(response, required_text[:int(len(required_text)/2)])

        min_overlap_req=min(min_overlap_req,int(len(required_text)/3))

        



        
        if len(overlap_req) >min_overlap_req:
            ind1 = response.find(overlap_req)
            ind2 = required_text.find(overlap_req)
            response_out = response[:ind1]+required_text[ind2:]

            return response_out,True

        else:

            return response,False
        
    else:
            return response,True
def apply_chatbot(chatbot,memory_object,inputs,outputs,prefix,required_text,state):
    """
    Applies Chatbot object
    Calls chatbot.truncate_input() to check and truncate input length
    Calls chatbot to get a list of results (batch size in AutogramConfig). Usually set to 1, can be more than 1 to give more chances to avoid banned phrases and get required text. 
    Post processes result if post processing was set in autogram config (it is by defult)
    updates 'model_turns' in mememory object to log args passed to chatbot and response
    """

    inputs,outputs,prefix = chatbot.truncate_input(inputs,outputs,prefix)

    responses,success = chatbot(inputs,outputs,prefix)


    if success:
        if chatbot.do_post_process:
            response,req_satisfied = post_process_responses(responses,required_text,chatbot.banned_phrases)
        else:
            response = responses[0]
            req_satisfied=True

    else:
        response = responses[0]
        req_satisfied=False
    memory_object.update_chatbot_log(inputs,outputs,prefix,response,state,req_satisfied)

    return response,req_satisfied


def apply_classifier(classifer,text,choices,memory_object,state,transition_probs):
    """
    Applies Classifier object
    Calls classifier.truncate_input() to check and truncate input length
    Calls classifier, get prediction  
    return index of prediction in list `choices`, as well as whether classifier succeeded 
    """


    text = classifer.truncate_input(text)
    #choices are either yes/no, or ABCD. Classifier logits are restricted to only allow tokens in choices
    answer_pred,success = classifer(text,answer_choices=choices,sim_probs=transition_probs)

    if answer_pred in choices:

        class_id = choices.index(answer_pred)
    else:
        print("WARNING. Classifier failed to predict valid answer")
        class_id=0
        success=False

    memory_object.update_classifier_log(text,choices,class_id,state,success)

    return class_id,success


def apply_template(starts,fins,texts,instruction_template):

    
    grouped = list(zip(starts,fins,texts))
    grouped = sorted(grouped)

    for elem in reversed(grouped):
        start,fin,text = elem
        instruction_template = instruction_template[:start]+text+instruction_template[fin:]




    return instruction_template


def count_states(state_trajectory,states):

    count = 0
    for state in states:
        for state2 in state_trajectory:
            if state==state2:
                count+=1
    return count
def predict_interjection_state(node_dict,inputs,outputs,classifier,memory_object,state,autogram_config):


    question = autogram_config.interjection_question
    answers=[]
    transitions=[]
    examples=[]
    probs=[]
    for key in node_dict.keys():
        node = node_dict[key]
        if not(node.condition_interjection is None) and len(node.condition_interjection)>0:
            answers.append(node.condition_interjection)
            transitions.append(node.name)
            examples.append(node.example_interjection)
            probs.append(node.probability_interjection)
    transitions.append(None)
    answers.append(autogram_config.interjection_default_answer)

    probs.append(1-np.sum(probs))
    probs = np.array(probs)



    abcde = "ABCDE"[:len(answers)]



    content=""

    for ex in examples:
        if not ex is None:
            content+=ex+"\n\n"
    

    content +=autogram_config.default_question_prompt+"\n\n"
    for i in range(len(inputs)):
        content +=outputs[i]+"\n\n"
        content +=inputs[i]+"\n\n"


    
    content+=question+"\n"
    yes_or_no=False


    for i in range(len(answers)):
        content+=abcde[i] + ". " +  answers[i] +"\n"

    choices=abcde

    class_id,success=apply_classifier(classifier,content,choices=choices,memory_object=memory_object,state=state,transition_probs=probs)  


    return transitions[class_id]
def process_node_id(new_node_id,memory_object,nodes,statement_interpreter):
    """
    Usually, new_node_id corresponds to another node in the graph, and the next step will be to simply move to that node.
    However, some special types of transitions do not, and require extra post processing

    These include:

        '.n' transitions -- a transition name with the suffix .n (for instance 'state1.n') is assumed to have 
            a different version ofstate for the nth visit to that state. 
            In the above example, it is expected that state1.1, state1.2 are defined, as well as state.3 etc if there are more
            Once the number of visits to states of this type is greater than the highest numbered state, then it will keep revisiting that state.
            So for instance if state1.1, state1.2, and state1.3 all exist then
                The first time it tranistions to state1.n it will go to state1.1
                The second time it tranistions to state1.n it will go to state1.2
                The third time it tranistions to state1.n it will go to state1.3
                The every additional time it tranistions to state1.n it will go to state1.3

            Note that if you'd prefer for the states to cycle back to state1.1 at the end, it is possible to implement that with .* states below (by downweighting a state each time it is visited)


        '.*' transitions -- a transition name with the suffix .* (for instance 'state1.*') is assumed to have several possible transitions. 
            In the above example, it is expected that state1.A, state1.B are defined, as well as state1.C etc. if there are more than 2 possibilities
            Each state gets a score computed for it, and the highest scoring state is selected
            As of the initial version, scores are calculated by which states visbale in the 'stored_states' in the memory object
            The attributes used to calculate scores include
                'prerequisite_states' - large pentalty (-1000) if these states haven't been visited
                'blocking_states' - large pentalty (-1000) if these states have been visited
                'up_weight_states' - small reward (+1) if these states have been visited
                'down_weight_states' - small penalty (-1) if these states have been visited
            We may later add other types of scores based on variables


        'return' -- pop the stack in the memory object, and return to the last function node and function scope.

        'quit' -- (not handled in this function) exits the while loop in the reply() function of the Autogram class, 
            and return the current response and memory object. This is the only way to do this outside of a Chat type Node 


    """

    #handle case where new_node_id is a variable
    if new_node_id[0]=="$":
        variable_dict = memory_object.get_variable_dict()
        new_node_id =str(variable_dict[new_node_id[1:]])
        



    state_trajectory = memory_object.get_stored_states()


    if new_node_id[:len("return")]=="return":
        return_statement = new_node_id

        if memory_object.get_stack_size()>1:
            
            new_node_id = memory_object.get_last_state_above() 

            memory_object.manage_return(return_statement)

            return new_node_id

        else:
            raise Exception("Reached return node outside of function")

    elif ".n" in new_node_id:
        node_prefix = new_node_id.split(".")[0]
        count=1
        found_all=False

        while not found_all:

            if node_prefix+"."+str(count) in state_trajectory:
                if node_prefix+"."+str(count+1) in nodes.keys():
                    count+=1
                else:
                    found_all=True

            else:
                found_all=True
        

        new_node_id=node_prefix+"."+str(count)

        return new_node_id




    elif ".*" in new_node_id:
        prefix = new_node_id.split(".")[0]
        allowed_nodes=[]

        best = ""
        max_score=-99999999

        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ".lower():
            node_name = prefix+"."+char 
            if node_name in nodes:
                allowed_nodes.append(node_name)
            else:
                break


        if nodes[allowed_nodes[0]].boolean_condition is None:
            use_score=True
        else:
            use_score=False

        counter=0
 
        for node_name in allowed_nodes:
        
            node = nodes[node_name]

            if not use_score:
                best=node_name
                

                if (counter<len(allowed_nodes)-1) and statement_interpreter.execute_expression(nodes[allowed_nodes[counter]].boolean_condition,memory_object.get_variable_dict()):
                    
                    break

            else:

                score=0.0
                if len(node.prerequisite_states)>0:
                    count = count_states(state_trajectory,node.prerequisite_states)
                    if count==0:
                        score-=10000

                if len(node.blocking_states)>0:
                    count = count_states(state_trajectory,node.blocking_states)
                    if count>0:
                        score-=10000

                count = count_states(state_trajectory,node.up_weight_states)
                
                score+=count
                count = count_states(state_trajectory,node.down_weight_states)

                score-=count

                if score>max_score:
                    best =  node_name
                    max_score=score

            counter+=1



        return best
     





    else:
        return new_node_id


def check_node_req(node,memory_object,include_last=False):
    """
    Checks required_revisit attribute. Used to check function calls. 
    Function will return empty string and never execute node it calls if node hasn't been revisited since last function call.
    """

    state_trajectory = memory_object.get_stored_states()

    if not include_last:

        state_trajectory = state_trajectory[:-1]
    for state in node.required_revisit:

        if state in state_trajectory:
            if node.name in state_trajectory:
                ind1 = state_trajectory.index(node.name)
                ind2 = state_trajectory.index(state)

                if ind2>ind1:
                    continue
                else:
                    return False
                
            else:
                continue


        else:
            return False
        
    return True

def matching_brackets(string):

    op= [] 
    dc = { 
        op.pop() if op else -1:i for i,c in enumerate(string) if 
        (c=='{' and op.append(i) and False) or (c=='}' and op)
    }
    return False if dc.get(-1) or op else dc

def find_occurrences(text, ch):
    occurrences = [i for i, letter in enumerate(text) if letter == ch]
    for i in reversed(range(len(occurrences))):
        occ = occurrences[i]


        if occ>0 and text[occ-1:occ+1]=='\$':
            occurrences = occurrences[:i]+occurrences[i+1]

    return occurrences


def get_variable(text,start):
    var_name = ""

    for i in range(start+1,len(text)):
        ch = text[i]
        if not(ch.isalnum() or ch=="_"):

            break
        else:
            var_name+=ch

    return var_name

def process_variable_string(text,variable_dict):
    """
    Replace text with variables like ( "Here is the context: $variable1") with the actual value of the variable.
    Returns empty string for whole string if 1 of more variable isn't defined
    """


    occurrences = find_occurrences(text, "$")
    new_text = text
    
    if len(occurrences)>0:
        
        for occ in reversed(occurrences):
            var_name=get_variable(text,occ)


            if len(var_name)==0:
                return ""
            else:


                if not var_name in variable_dict.keys() or variable_dict[var_name] is None:
                    return ""
                else:
                    new_text = new_text[:occ]+str(variable_dict[var_name])+new_text[occ+len(var_name)+1:]
                    

    else:
        
        return text
    
    
    return new_text

def remove_assignment(instruction):


    var_name,instruction = split_assignment(instruction)

    return instruction
    

        



def set_variables(instruction ,variable_dict,is_inst=True):
    """
    Assings variables to an instruction.
    As of initial version, variables can be in between brackets and must start with $ sign
    For instance, and instruction might say

    ""
    {Here is some additional context: $context}
    Reply to the user and answer their question.
    ""

    If the variable $context in the memory object and has a length greater than 0, the string value of that variable will replace $context
    Otherwise, the entire string in brackets will be removed from the instruction. 

    """

    if is_inst:
        instruction=remove_assignment(instruction)


    lb = find_occurrences(instruction,"{")
    rb = find_occurrences(instruction,"}")

    if len(lb)>0 and len(rb)>0:
        if len(lb)>len(rb):
            lb = lb[:len(rb)]
        elif len(lb)<len(rb):
            rb = rb[:len(lb)]


        bracket_dict=dict(zip(lb,rb))


    
        bracket_list = reversed(sorted(list(bracket_dict.keys())))
       
        for start in bracket_list:
            fin = bracket_dict[start]
            bracketed_text = instruction[start+1:fin]
            replaced_text = process_variable_string(bracketed_text,variable_dict)



            instruction = instruction[:start]+replaced_text+instruction[fin+1:]



    if len(instruction)>0:
        new_instruction = process_variable_string(instruction,variable_dict)

        if len(new_instruction)==0:
            raise Exception("The following instruction has undefined variables: "+instruction)
        else:
            instruction=new_instruction
    
    


                



    return instruction


def check_contains_variables(instruction ,memory_object,is_inst=True):
    """
    Similar to set variables, but instead returns a boolean
    Returns True if the processed instruction has at least one variable set
    Mainly used to determine if we should retain the instruction for a turn when giving the prompt in later turns
    If that previous instruction contained a variable, it may have important information
    """

    if is_inst:
        instruction=remove_assignment(instruction)


    lb = find_occurrences(instruction,"{")
    rb = find_occurrences(instruction,"}")
    bracket_dict = matching_brackets(instruction)

    if len(lb)>0 and len(rb)>0:
        if len(lb)>len(rb):
            lb = lb[:len(rb)]
        elif len(lb)<len(rb):
            rb = rb[:len(lb)]


        bracket_dict=dict(zip(lb,rb))





    if bracket_dict:

        if len(bracket_dict.keys())>0:
            bracket_list = reversed(sorted(list(bracket_dict.keys())))
            for start in bracket_list:
                fin = bracket_dict[start]
                bracketed_text = instruction[start+1:fin]
                replaced_text = process_variable_string(bracketed_text,memory_object)
                if len(replaced_text)>0:
                    return True
    return False




def process_cell(x):

    if type(x)==str:
        if len(x)>0:
            return x
        

    else:
        if not np.isnan(x):
            return str(x)
        else:
            return None
        
        
    return None



def test_transitions(nodes):
    """
    Simulate transitions.
    As of initial version, still need to fix for .* and .n states
    """
    for node_name in nodes.keys():
        transitions = nodes[node_name].transitions
        for state in transitions:
            if state[:len("return")]=="return":
                continue
            if state=="quit":
                continue
            if ".*" in state:
                continue
            if ".n" in state:
                continue
            proc_state = state 

            if not (proc_state in nodes.keys()):
                raise Exception("Error for state " + str(node_name ) + ". Invalid transition state: " +state)

def get_interjection_states(nodes):
    internodes=[]
    for key in nodes.keys():

        if nodes[key].condition_interjection is not None:
            internodes.append(nodes[key])

    return internodes

def simulate_interjections(node_dict,turn_num,min_turns=3,max_turns=50):

    if turn_num>=max_turns:
        terminate=True
    else:
        terminate=False

    state_keys = list(node_dict.keys())

    random.shuffle(state_keys)

    
    for key in node_dict.keys():
        state = node_dict[key]
        if state.condition_interjection is not None:
            if state.terminal:
                if terminate:
                    return state.name
                if turn_num>=min_turns:
                    if random.random()<state.probability_interjection:
                        return state.name
                    
        
            else:
                if terminate:
                    continue
                else:
                    if random.random()<state.probability_interjection:
                        return state.name
                    

    return None



def split_assignment(statement):
    try:
        #if statement is valid python, we assume it is a function or python_function node and parse it accordingly
        module = ast.parse(statement)
        if isinstance(module.body[0],ast.Assign):
            var_name = module.body[0].targets[0].id

            expression = ast.unparse(module.body[0].value)
        else:
            var_name=None
            expression=statement
    except:
        #non-function call instructions will usually be invalid python statements and need to be parsed seperately
        

        occs = find_occurrences(statement,"=")
        if len(occs)>0:
            
            ind = occs[0]
            var_name = statement[:ind].replace(" ","")
            expression = statement[ind+1:]
            while expression[0]==" ":
                expression=expression[1:]


            
        else:
            var_name=None
            expression = statement

        



    return var_name,expression

def get_assignment(statement):
    try:
        #if statement is valid python, we assume it is a function or python_function node and parse it accordingly
        module = ast.parse(statement)
        if isinstance(module.body[0],ast.Assign):
            var_name = module.body[0].targets[0].id
            
        else:
            var_name=None
    except:
        #non-function call instructions will usually be invalid python statements and need to be parsed seperately
        #statement = statement.replace("\=",PLACEHOLDER_STR4)
        occs = find_occurrences(statement,"=")
        if len(occs)>0:
            ind = occs[0]
            var_name = statement[:ind].replace(" ","")
        else:
            var_name=None



    return var_name
    

def get_function(statement):
    module = ast.parse(statement)

    return module.body[0].value.func.id+"()"
    

def parse_function(statement,variable_dict,statement_interpreter):
    module = ast.parse(statement)
    if isinstance(module.body[0],ast.Assign):
        var_name = module.body[0].targets[0].id
        
    else:
        var_name=None
    function = module.body[0].value
    func_name = function.func.id+"()"


    new_args = []

    for arg in function.args:
        if isinstance(arg,ast.Name):
            new_args.append(variable_dict[arg.id])
        else:
            code = ast.unparse(arg)
            new_args.append(statement_interpreter.execute_expression(code, variable_dict))




    return var_name,func_name,new_args


def python2df(**kwargs):


    if 'transitions' in kwargs and not kwargs['transitions'] is None:
        kwargs['transitions']=",".join(kwargs['transitions'])

    if 'transition_probs' in kwargs and not (kwargs['transition_probs'] is None):
        split=[str(x) for x in kwargs['transitions_probs']]
        kwargs['transitions_probs'] = ",".join(split)

    if 'prerequisite_states' in kwargs and not kwargs['prerequisite_states'] is None:
        kwargs['prerequisite_states']=",".join(kwargs['prerequisite_states'])

    if 'blocking_states' in kwargs and not kwargs['blocking_states'] is None:
        kwargs['blocking_states']=",".join(kwargs['blocking_states'])
    if 'up_weight_states' in kwargs and not kwargs['up_weight_states'] is None:
        kwargs['up_weight_states']=",".join(kwargs['up_weight_states'])
    if 'down_weight_states' in kwargs and not kwargs['down_weight_states'] is None:
        kwargs['down_weight_states']=",".join(kwargs['down_weight_states'])

    if 'required_revisit' in kwargs and not kwargs['required_revisit'] is None:
        kwargs['required_revisit']=",".join(kwargs['required_revisit'])

    chars = 'abcdefghijklmnopqrstuvwxyz'
    if 'transition_choices' in kwargs and not kwargs['transition_choices'] is None:
        transition_choices=kwargs['transition_choices']
    

        for i in range(len(transition_choices)):

            if not transition_choices[i] is None:


                kwargs['transition_choice_'+chars[i]] = transition_choices[i]
    if 'transition_choices' in kwargs:
        del kwargs['transition_choices']



    if 'user_instruction_transitions' in kwargs and not kwargs['user_instruction_transitions'] is None:
        user_instruction_transitions=kwargs['user_instruction_transitions']
    

        for i in range(len(user_instruction_transitions)):

            if not user_instruction_transitions[i] is None:


                kwargs['user_instruction_transition_'+chars[i]] = user_instruction_transitions[i]
    if 'user_instruction_transitions' in kwargs:
        del kwargs['user_instruction_transitions']

    return kwargs



                
def df2python(**kwargs):



    if 'transitions' in kwargs and not kwargs['transitions'] is None:
        
        kwargs['transitions']=proc_comma_field(kwargs['transitions'])


    if 'transition_probs' in kwargs and not (kwargs['transition_probs'] is None):
        split=kwargs['transitions_probs'].split(",")
        kwargs['transitions_probs']=[float(x.replace(" ","")) for x in split]

    if 'prerequisite_states' in kwargs and not kwargs['prerequisite_states'] is None:
        
        kwargs['prerequisite_states']=proc_comma_field('prerequisite_states')

    if 'blocking_states' in kwargs and not kwargs['blocking_states'] is None:
        kwargs['blocking_states']=proc_comma_field('blocking_states')
    if 'up_weight_states' in kwargs and not kwargs['up_weight_states'] is None:
        kwargs['up_weight_states']=proc_comma_field('up_weight_states')
    if 'down_weight_states' in kwargs and not kwargs['down_weight_states'] is None:
        kwargs['down_weight_states']=proc_comma_field('down_weight_state')

    if 'required_revisit' in kwargs and not kwargs['required_revisit'] is None:
        kwargs['required_revisit']=proc_comma_field('required_revisit')


    transition_choices=[]
    for char in 'abcdefghijklmnopqrstuvwxyz':

        if 'transition_choice_'+char in kwargs:
            if not(kwargs['transition_choice_'+char] is None):
            
                transition_choices.append(kwargs['transition_choice_'+char])
            del kwargs['transition_choice_'+char]

    if len(transition_choices)>0:

        kwargs['transition_choices']=transition_choices


    user_instruction_transitions=[]
    for char in 'abcdefghijklmnopqrstuvwxyz':

        if 'user_instruction_transition_'+char in kwargs:
            if not(kwargs['user_instruction_transition_'+char] is None):
            
                user_instruction_transitions.append(kwargs['user_instruction_transition_'+char])
            del kwargs['user_instruction_transition_'+char]
    if len(user_instruction_transitions)>0:
        kwargs['user_instruction_transitions']=user_instruction_transitions


    return kwargs




def proc_comma_field(field):
    fields = field.split(",")
    new_fields =[]

    #removes leading and trailing spaces
    for x in fields:
        while True:
            if x[0]==" ":
                x=x[1:]
            elif x[-1]==" ":
                x=x[:-1]
            else:
                new_fields.append(x)
                break

    return new_fields 