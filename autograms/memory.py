
from .autogram_utils import get_variable, get_assignment
#from .__init__ import __version__

class MemoryObject():
    """
    Wrapper object around a dictionary/json type object that stores conversation history and variables
    memory_dict stores memory

    fields of memory_dict:
        'stack' - The core memory used by the system. A list of dictionaries that tracks memory at each function scope level
        'model_turns' - Mainly for logging/debugging. A list of inputs given to every call to the classifier and chatbot, as well as the response/prediction from the classifier/chatbot
        'state_trajectory' - stores a list of dictionaries corresponding to each node visited
        'version' - the autograms version that created the memory object. If the structure of the memory object changes, version will be used for mapping memory objects from old versions of autograms to new ones.
    
    Calling a function increases length of stack by 1, and return statement pops last element
    
    fields of each stack element:
        'turns' - list of dictionaries that describe different types of inputs, the output, and other fields associated with each node call
        'last_state' - last state corresponding to node at which apply_instruction() function was called
        'variables' - dictionary keeping track of all variables at that layer of the stack
        'prompt' - prompt at that layer of the stack. Initialized to default prompt in AutogramConfig object, can be changed with `set_prompt` and `append_prompt` node types.
        'user_prompt' - user prompt at that layer of the stack. Initialized to default user_prompt in AutogramConfig object, can be changed with `set_user_prompt` and `append_user_prompt` node types.
        'function_scope' - type of function that called the level of the state. Can either be 'normal', 'local', 'global' 
                'normal' - corresponds to FunctionNode. Sees previous layer of stack (as well as any layers previous layer can see), resets to default prompts, erases stack layer and elements return is hit 
                'local' - corresponds to LocalFunctionNode. Doesn't see previous layers of stack, only can access variables that are passed as function arguments. Erases stack layer after return.
                'global' - corresponds to GlobalFunctionNode. Sees all previous layer of the stack (as well as any layers previous layer can see), keeps prompts of previous layer, and adds all fields to above layer after return.
    
    """


    def __init__(self,autogram_config,memory_dict=None):
        """
        args:
            autogram_config - AutogramConfig object
            memory_dict - dictionary that defines memory
        """

        from . import __version__

        if memory_dict is None:

            self.memory_dict=dict()
            self.memory_dict['stack']=[{"turns":[],"last_state":"","variables":{}, "prompt":autogram_config.default_prompt,"user_prompt":autogram_config.default_user_prompt,"function_scope":"normal"}]
            if autogram_config.log_model_turns:
                self.memory_dict['model_turns']=[]


            self.memory_dict["state_trajectory"]=[]


            #we may later use this to maintain backward compatibiltiy if future memory objects have different structure
            self.memory_dict["version"] = __version__
        
               

        else:
            

            self.memory_dict=memory_dict

        self.default_prompt = autogram_config.default_prompt
        self.default_user_prompt = autogram_config.default_user_prompt





    def get_last_state(self):
        """
        returns:
            last_state - state name of last node of top layer of stack where node.apply_instruction() was called
        """
        return self.memory_dict['stack'][-1]['last_state']



    def get_last_variable_output(self):
        """
        returns:
            _last_variable_output - value stored in _last_variable_output in variables of top layer of stack, corresponding to the output of the last node.get_variable_output() call
        """ 
        if '_last_variable_output' in self.memory_dict['stack'][-1]['variables'].keys():
            return self.memory_dict['stack'][-1]['variables']['_last_variable_output']
        else:
            return None
        
    def set_variable(self,name,value):

        self.memory_dict['stack'][-1]['variables'][name]= value

        

    def get_last_reply(self):

        """
        returns:
            last_agent_reply - last output from model, or None if previous node type didn't have model output (for instance PromptModiferNode type nodes)
        """ 
        if len(self.memory_dict['stack'][-1]['turns'])>0:
            return self.memory_dict['stack'][-1]['turns'][-1]['agent_reply']
        else:
            return None
        

    def get_last_instruction(self):
        """
        returns:
            last_instruction - last instruction given to the model
        """ 
        if len(self.memory_dict['stack'][-1]['turns'])>0:
            return self.memory_dict['stack'][-1]['turns'][-1]['instruction']
        else:
            return None
    def get_prompt(self):
        """
        returns:
            prompt- prompt at top layer of the stack
        """ 
        return self.memory_dict['stack'][-1]['prompt']
    def get_last_state_above(self):
        """
        returns:
            last_state_above - this gives the state that called the function that the autogram is currently in. We need to get this state to return.
        """ 
        if len(self.memory_dict['stack'])>1:
            return self.memory_dict['stack'][-2]['last_state']
        else:
            return None
        
    def get_stack_size(self):
        """
        returns:
            stack_size --length of stack, describes the depth of nested function calls
        """ 
        return len(self.memory_dict['stack'])
    

    def get_user_prompt(self):
        """
        returns:
            user_prompt- user prompt at top layer of the stack
        """ 
        return self.memory_dict['stack'][-1]['user_prompt']
    def get_thought_chat_turns(self):
        """
        returns:
            turns -- list of thought and chat turns in current scope
        """ 
        turns=[]
        for i in reversed(range(len(self.memory_dict['stack']))):

            new_turns = []

            for turn in self.memory_dict['stack'][i]['turns']:
                if turn["is_reply"] or turn["is_thought"]:
                    new_turns.append(turn)
            

            turns = new_turns+ turns

            scope = self.memory_dict['stack'][i]['function_scope']

            if scope=="local":
                break
        return turns

    def get_user_replies(self):
        """
        returns:
            user_replies- list of replies from user in current scope
        """ 
        user_replies=[]
        for i in reversed(range(len(self.memory_dict['stack']))):


            new_user_replies=[]

            for j in range(len(self.memory_dict['stack'][i]['turns'])):
                if self.memory_dict['stack'][i]['turns'][j]['is_reply']:
                    new_user_replies.append(self.memory_dict['stack'][i]['turns'][j]['user_reply'])
            user_replies = user_replies + new_user_replies

            scope = self.memory_dict['stack'][i]['function_scope']

            if scope=="local":
                break

        return user_replies
    def get_agent_replies(self):
        """
        returns:
            agent_replies- list of replies from agent in current scope
        """ 
        agent_replies=[]
        for i in reversed(range(len(self.memory_dict['stack']))):

            new_agent_replies=[]
            for j in range(len(self.memory_dict['stack'][i]['turns'])):
                if self.memory_dict['stack'][i]['turns'][j]['is_reply']:
                    new_agent_replies.append(self.memory_dict['stack'][i]['turns'][j]['agent_reply'])

    

            agent_replies = new_agent_replies+agent_replies

            scope = self.memory_dict['stack'][i]['function_scope']

            if scope=="local":
                break

        return agent_replies

    def get_state_categories(self):
        """
        returns:
            categories -- returns list of state categories in current scope
        """ 
        categories=[]
        for i in reversed(range(len(self.memory_dict['stack']))):

            new_categories = [self.memory_dict['stack'][i]['turns'][j]['categories'] for j in range(len(self.memory_dict['stack'][i]['turns']))]
            categories= categories + new_categories

            scope = self.memory_dict['stack'][i]['function_scope']

            if scope=="local":
                break

        return categories
    def get_turn_attribute(self,attribute):
        """
        args:
            attribute -- name of a turn attribute to get
        returns:
            att_list -- returns list of attribute in current scope
        """ 
        att_list=[]
        for i in reversed(range(len(self.memory_dict['stack']))):

            new_att_list = [self.memory_dict['stack'][i]['turns'][j][attribute] for j in range(len(self.memory_dict['stack'][i]['turns']))]
            att_list= att_list + new_att_list

            scope = self.memory_dict['stack'][i]['function_scope']

            if scope=="local":
                break

        return att_list
    def get_turns(self):
        """
        returns:
            turns -- get a list of all turns in the current scope
        """ 
        turns=[]
        for i in reversed(range(len(self.memory_dict['stack']))):


            turns = self.memory_dict['stack'][i]['turns'] + turns

            scope = self.memory_dict['stack'][i]['function_scope']

            if scope=="local":
                break
        return turns

    def get_stored_states(self):
        """
        returns:
            stored_states -- get a list of all stored states
        """ 
        stored_states=[]
        for i in reversed(range(len(self.memory_dict['state_trajectory']))):

            stored_states.append(self.memory_dict['state_trajectory'][i]['state'])


        return stored_states

    def get_variable_dict(self,prev_scope=False):
        """
        returns:
            variable_dict -- get the variables in the current scope
            prev_scope -- when applying transitions form function calls, sometimes needs to access previous scope after stack has been extended
        """ 
        variable_dict=dict()
        for i in reversed(range(len(self.memory_dict['stack']))):
            if prev_scope:
                prev_scope=False
                continue


            for var_name in self.memory_dict['stack'][i]['variables'].keys():
                variable_dict[var_name]=self.memory_dict['stack'][i]['variables'][var_name]

            scope = self.memory_dict['stack'][i]['function_scope']

            if scope=="local":
                break

        return variable_dict
      
        
    
    def append_turn(self,state,category,instruction,agent_reply,user_reply,retain_instruction,is_reply=False,is_thought=False):
        """
        args:
            state -- name of state, corresponsonding to node.name
            category -- category of state. Used in combination with conv_scope attribute to select states from only 1 category
            instruction -- processed instruction used by the model
            agent_reply -- model's reply
            user_reply -- user's reply model was responding to, or "" if model was only responding to instruction
            retain_instruction -- boolean, determines whether we will continue to show the instruction for this turn when showing prompt for future turns
            is_reply -- whether this node replied to the user. True for chat nodes, False for most other nodes
        """ 
        
       # retain_instruction=str(int(retain_instruction))

        self.memory_dict['stack'][-1]['turns'].append({"state":state,"category":category,"instruction":instruction,"agent_reply":agent_reply,"user_reply":user_reply,"retain_instruction":retain_instruction,"is_reply":is_reply,"is_thought":is_thought})
        if (not (user_reply is None)) and (len(user_reply)>0):
            self.memory_dict['stack'][-1]['variables']["_last_user_reply"]=user_reply
        self.memory_dict['stack'][-1]['variables']["_last_state"]=state
        
    def append_state(self,state):
        """
        sets last state, and appends stored_states to current top of stack
        args:
            state -- name of state, corresponsonding to node.name
        """
        self.memory_dict['stack'][-1]['last_state'] = state

        self.memory_dict['state_trajectory'].append({"state":state})

    def set_prompt(self,text):
        """
        sets prompt, used by SetPromptNode
        args:
            text -- string of prompt to set
        """
        self.memory_dict['stack'][-1]['prompt']=text
    def append_prompt(self,text):
        """
        appends prompt, used by AppendPromptNode
        args:
            text -- string of prompt to append
        """
        self.memory_dict['stack'][-1]['prompt']+="\n"+text
    def set_user_prompt(self,text):
        """
        sets user prompt, used by SetUserPromptNode
        args:
            text -- string of prompt to set
        """
        self.memory_dict['stack'][-1]['user_prompt']=text
    def append_user_prompt(self,text):
        """
        appends user prompt, used by AppendUserPromptNode
        args:
            text -- string of prompt to append
        """
        self.memory_dict['stack'][-1]['user_prompt'] += "\n"+text

    def assign_variables(self,node,variable_output):
        """
        Assigns variables to top of stack, usually using the output of node.get_variable_output(), which gives variable output for a node. 
        Special variable called "_last_variable_output" is set after every turn
        Any variable assignments defined in the instruction using '=' symbol are also set here

        args:
            node -- previosly executed node
            variable_output -- variable output from previously executed node
        """


        self.memory_dict['stack'][-1]["variables"]["_last_variable_output"] = variable_output


        var_name = get_assignment(node.instruction)

        

        if not var_name is None:

            self.memory_dict['stack'][-1]["variables"][var_name] = variable_output
            

    def update_chatbot_log(self,inputs,outputs,prefix,response,state,success):
        """
        Adds a turn for a chatbot reply to the log defined under "model_turns" 
        args:
            inputs - Previous (and current) inputs to model, corresponding to instructions or user replies (or both)
            outputs - Previous outputs from the model
            prefix - start of reply (if used, only allowed for completion style models)
            response - response from model at the current turn
            state - node.name at the current turn
            success - whether the model api worked successfully without needing to generate any banned phrases
        """
        if "model_turns" in self.memory_dict.keys():

            if success:
                success=1
            else:
                success=0

            self.memory_dict["model_turns"].append({"model":"chatbot","input_history":inputs,"output_history":outputs,"reply_prefix":prefix,"model_response":response,"state":state,"success":success})




    def update_classifier_log(self,text,choices,class_id,state,success):
        """
        Adds a turn for a classifier prediction to the log defined under "model_turns" 
        args:
            text -- input text to classifier
            choices -- multiple choice options fro classifier
            class_id -- predicted class index by classifier
            state - node.name at the current turn
            success - whether the model worked successfully
        """
        if "model_turns" in self.memory_dict.keys():
            if success:
                success=1
            else:
                success=0

            self.memory_dict["model_turns"].append({"model":"classifier","input_text":text,"choices":choices,"class_pred":class_id,"state":state,"success":success})
     



    def manage_return(self,return_statement):

        """
        Handles returns from function calls. Pops the top level of the stack. Has different behavior depending on function_scope of stack layer.
        For all functions, special variable called '_return_variable_output' is set when function is returned. This will either be the variable output of the last node inside the function call, or a variable defined in the return statement
        args:
            return_statement: optional statement that controls which variable is returned (ex: return $variable1). If not return statement is simply `return`, special variable _last_variable_output is returned (see assign_variables())
        """

        scope = self.memory_dict['stack'][-1]['function_scope']

        
        if len(return_statement.split(" "))>1:
            #assumes a variable name in return statement, return this variable
            var_name=return_statement.split(" ")[1] 
            self.memory_dict['stack'][-2]['variables']['_return_variable_output'] =  self.memory_dict['stack'][-1]['variables'][var_name]
        
        
        elif "_last_variable_output" in self.memory_dict['stack'][-1]['variables']:
            #otherwise return _last_variable_output if it exists. This willbe variable output of last node in function call
            self.memory_dict['stack'][-2]['variables']['_return_variable_output'] =  self.memory_dict['stack'][-1]['variables']["_last_variable_output"]
            del self.memory_dict['stack'][-1]['variables']["_last_variable_output"]
        else:
            self.memory_dict['stack'][-2]['variables']['_return_variable_output'] = None


        if scope=="local":
            #local scope fully deletes the top layer of the stack without retaining anything (other than logging in memory_dict['model_turns'] if set)
            del self.memory_dict['stack'][-1]
        elif scope=='global':
            #global scope retains everything from function call and appends it to previous scope when returning. Prompts that are set in global functions also overwrite the prompts when returning


            variables = self.memory_dict['stack'][-1]['variables']

            self.memory_dict['stack'][-2]['turns'] +=self.memory_dict['stack'][-1]['turns'] 

           # self.memory_dict['stack'][-2]['stored_states'] +=self.memory_dict['stack'][-1]['stored_states']
            for key in variables.keys():
                self.memory_dict['stack'][-2]['variables'][key]=variables[key]


            self.memory_dict['stack'][-2]['prompt'] =self.memory_dict['stack'][-1]['prompt']
            self.memory_dict['stack'][-2]['user_prompt'] =self.memory_dict['stack'][-1]['user_prompt']
            self.memory_dict['stack'][-2]['last_state'] =self.memory_dict['stack'][-1]['last_state']


            del self.memory_dict['stack'][-1]


        elif scope=='normal':

           # self.memory_dict['stack'][-2]['stored_states'] +=self.memory_dict['stack'][-1]['stored_states']
            del self.memory_dict['stack'][-1]
            
        else:
            raise Exception("Invalid scope type "+str(scope))
        


    def finalize_return(self):
        """
        gets variable output from return, and deletes temporary return variable
        returns:
            variable_output - variable from function return
        """

       
        variable_output= self.memory_dict['stack'][-1]['variables']["_return_variable_output"]

        del self.memory_dict['stack'][-1]['variables']["_return_variable_output"]


        return variable_output
       

    def is_return(self):
        """
        Checks if a function node is in the process of returning. 
        Useful to distinguish first visit to function node (is_return will be False) from second visit once function returns (is_return will be True)
        returns:
            is_return: whether or not function is in process of returning
        """
        is_return = "_return_variable_output" in self.memory_dict['stack'][-1]['variables']
        return is_return


    def is_call(self):
        """
        Checks if a function is in the process of calling. 
        returns:
            is_call: whether or not function node is in process of calling a function
        """
        is_call=len(self.memory_dict['stack'])>1 and len(self.memory_dict['stack'][-1]["last_state"])==0
        return is_call

    def manage_call(self,variable_dict,function_scope):
        """
        Appends the stack when a function is called 
        args:
            variable_dict -- variables that the new scope will be initialized with
            function_scope -- function scope type, "normal", "global", or "local"
        """
        if function_scope=="global" or function_scope=="normal":
            prev_prompt = self.memory_dict['stack'][-1]['prompt']
            prev_user_prompt = self.memory_dict['stack'][-1]['user_prompt']
            self.memory_dict['stack'].append({"turns":[],"last_state":"","variables":variable_dict, "prompt":prev_prompt,"user_prompt":prev_user_prompt,"function_scope":function_scope})
        
        else:
            self.memory_dict['stack'].append({"turns":[],"last_state":"","variables":variable_dict, "prompt":self.default_prompt,"user_prompt":self.default_user_prompt,"function_scope":function_scope})
        

    def set_python_return(self,variable_output):

        self.memory_dict['stack'][-1]['variables']["_python_variable_output"]=variable_output
        

        
    def pop_python_return(self):
        variable_output= self.memory_dict['stack'][-1]['variables'].pop("_python_variable_output")

        return variable_output


    def get_dict(self):
        """
        get memory dictionary that keeps track of memory
        returns:
            memory_dict --  memory dictionary that keeps track of memory 
        """
        return self.memory_dict
    def set_dict(self,memory_dict):
        """
        set memory dictionary that keeps track of memory 
        args:
            memory_dict --  memory dictionary that keeps track of memory
        """
        self.memory_dict=memory_dict




def get_version():
    setup_path = os.path.join(os.path.dirname(__file__), 'setup.py')
    with open(setup_path, 'r') as f:
        content = f.read()
    version_match = re.search(r"version\s*=\s*['\"]([^'\"]*)['\"]", content)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")
