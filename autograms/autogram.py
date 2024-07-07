

from .autogram_config import AutogramConfig
from .nodes import  BaseNode
import ast

import json
from collections import OrderedDict
from .memory import MemoryObject
from .graph_utils import get_graph
from .autogram_utils import  process_node_id, post_process_user_responses, process_cell, simulate_interjections, get_interjection_states,python2df,df2python
from .statement_interpreter import StatementInterpreter
from .models import CHATBOT_TYPES, CLASSIFIER_TYPES
from .nodes import NODE_TYPES, EXPECTED_FIELDS
import os





import time
import copy






class Autogram():

    """
    Autogram is the class that executes a program defined by a set of nodes and their associated attributes
    It holds autogram.nodes, which is a dictionary of all the nodes that have been loaded.
    It contains functions to reply to the user, simulate the user's reply, or call any callable AutoGRAMS module as a function
    """
   
    def __init__(self,autogram_config=None,df=None,api_keys={},allow_incomplete=None):

        """
        Initializes autogram object
        Args:
            autogram_config - object of type AutogramConfig that defines all the autogram settings, default prompts, and prompt tempalaes
            df - DataFrame object that results from loading the spreadsheet. if df is included, nodes will be defined when autogram is initialized.
            api_keys - dictionary where keys are model type (ex: 'openai') and values are api keys
            allow_incomplete - boolean, allows an autogram to be defined without valid api keys or fully connected nodes
        """

        if allow_incomplete is None:
            if autogram_config is None or df is None:
                allow_incomplete=True
            else:
                allow_incomplete=False



        if autogram_config is None:
            autogram_config = AutogramConfig()
        
        if autogram_config.self_referential:
            #nodes with python_function can access and modify the autogram, requires coding autogram with care
            autogram_config.python_modules["self"]=self
        self.config = autogram_config

         
        new_api_keys={}
        if "load_from_env" in api_keys:
            load_from_env=api_keys["load_from_env"]
        else:
            load_from_env=False

        for key in api_keys:
            if not(key=="load_from_env"):
                if load_from_env:
                    new_api_keys[key] = os.environ[api_keys[key]]
                else:
                    new_api_keys[key]=api_keys[key]

        self.api_keys = new_api_keys
        self.allow_incomplete=allow_incomplete
        self.statement_interpreter = StatementInterpreter(autogram_config,self.api_keys)

        if allow_incomplete:
            try:
            #dictionaries CHATBOT_TYPES and CLASSIFIER_TYPES store the allowable chatbots and classifier classes
                self.chatbot = CHATBOT_TYPES[autogram_config.chatbot_type](autogram_config,self.api_keys)
                self.classifier = CLASSIFIER_TYPES[autogram_config.classifier_type](autogram_config,self.api_keys,chatbot=self.chatbot)
                self.user_bot = CHATBOT_TYPES[autogram_config.chatbot_type](autogram_config,self.api_keys,chatbot=self.chatbot)
            except:
                self.chatbot =None
                self.classifier=None
                self.user_bot =None
                print("Warning, some model API keys are missing. This autogram will give errors if models are called.")


        else:
            #dictionaries CHATBOT_TYPES and CLASSIFIER_TYPES store the allowable chatbots and classifier classes
            self.chatbot = CHATBOT_TYPES[autogram_config.chatbot_type](autogram_config,self.api_keys)
            self.classifier = CLASSIFIER_TYPES[autogram_config.classifier_type](autogram_config,self.api_keys,chatbot=self.chatbot)
            self.user_bot = CHATBOT_TYPES[autogram_config.chatbot_type](autogram_config,self.api_keys,chatbot=self.chatbot)

        #NODE_TYPES is a dictionary where the keys are the allowable action names and values are the corresponding node classes
        self.node_types=NODE_TYPES

        #EXPECTED_FIELDS is a list of all allowable fields
        self.expected_fields=EXPECTED_FIELDS

        #default initial state ofr autogram, set to "start1" if not changed
        self.start_state=autogram_config.start_state

        
        self.test_mode=False
  
        self.nodes= OrderedDict()
        self.node_args=list()

        if not df is None:
            #loads nodes into autogram from data frame
            self.add_nodes_from_data_frame(df)

            #tests added nodes and update neccesary variables
            self.update()



        


    def update(self,include_inst=False,finalize=True):

        """
        Call update once all nodes have been loaded. If finalize is True or allow incomplete is False, it tests the graph for errors. It also updates the interjection nodes, which are nodes that can be reached from any chat state.
        """

        if finalize==True:
            self.allow_incomplete=False
        

        #test_transitions(self.nodes)
        graph = get_graph(self.nodes,allow_undefined=self.allow_incomplete,include_inst=include_inst)
        self.graph=graph
        

        
        self.inter_nodes = get_interjection_states(self.nodes)


    def update_api_keys(self,api_keys):

        new_api_keys={}
        if "load_from_env" in api_keys:
            load_from_env=api_keys["load_from_env"]
        else:
            load_from_env=False

        for key in api_keys:
            if not(key=="load_from_env"):
                if load_from_env:
                    new_api_keys[key] = os.environ[api_keys[key]]
                else:
                    new_api_keys[key]=api_keys[key]

        self.api_keys = new_api_keys
        self.statement_interpreter = StatementInterpreter(self.config,self.api_keys)

        if self.chatbot is None:
            self.chatbot = CHATBOT_TYPES[self.config.chatbot_type](self.config,self.api_keys)
            self.classifier = CLASSIFIER_TYPES[self.config.classifier_type](self.config,self.api_keys,chatbot=self.chatbot)
            self.user_bot = CHATBOT_TYPES[self.config.chatbot_type](self.config,self.api_keys,chatbot=self.chatbot)






    def reply(self,user_reply="",memory_object=None,memory_dict=None,set_state=None,test_mode=False,return_as_dict=False):
        """
        Function to reply when a new user response is received. This function will apply nodes and transitions until it reaches a node that allows a reply (usually a chat type node)
        Args:
            user_reply - string that gives last user reply
            memory_object - MemoryObject that keeps track of memory of conversation history, states, and variables. Will define memory_object from memory_dict if memory_object isn't defined
            memory_dict - json like dictionary that defines memory object. If both memory_object and memory_dict are undefined, will initialize new memory_object.
            set_state - string that gives starting state, can be used to override the last state stored in the memory object. Not needed otherwise.
            test_mode - running in test modes mean that all models and APIs will give a default response. Useful for quickly testing random trajectories through graph
            return_as_dict - if False, returns MemoryObject, otherwise returns dictionary that defines memory object
        Returns:
            response - string that gives model's response to user_reply
            memory_object (or memory_dict if return_as_dict is set) - MemoryObject that keeps track of conversation history, states, and variables
        """
        response_to_user=False
        response=None
    


        self.test_mode = test_mode
        self.chatbot.set_test_mode(test_mode)
        self.classifier.set_test_mode(test_mode)

        if memory_object is None:
            
            memory_object = MemoryObject(self.config,memory_dict)


        last_state = memory_object.get_last_state()

        if len(last_state)==0:
  
            #set node to start state if not defined
            if self.start_state in self.nodes.keys():
                set_state = self.start_state
            else:
                set_state = list(self.nodes.keys())[0]


        
        else:

            node = self.nodes[last_state]



        

        #keep iterating until we hit a node that gives a response meant for user
        while not response_to_user:


            if not(set_state is None):

                #force next state to be set_state
                new_node_id=set_state
                node = self.nodes[new_node_id]
                set_state=None


            else:

                
                """
                get variable that previous node output
                each node type can have different get_variable_output function, with base behavior defined in BaseNode
                most common is to output the reply from the model or output of a function. Some node types have no/empty variable output
                """
                variable_output = node.get_variable_output(user_reply,memory_object)


                #temporarily assigns variable output to variable 'last_variable_output'. Will also asisgn it to any variables defined in the node's instruction
                memory_object.assign_variables(node,variable_output)

                """
                Get the next node id using the nodes transition function. Each node type can have a different apply_transition, with base behavior defined in BaseNode
                if only 1 transition is defined, will usually return this
                if multiple transitions are defined, will use classifier model to answer a multiple choice question defined for previously executed the node to determine new node
                """
                new_node_id = node.apply_transition(user_reply,memory_object,self.classifier,self.nodes,self.config)

                """
                certain node names need additional processing
                for instance "return" transitions go back to the function that called them
                transitions that end in .* implement wildcard transitions
                """
                new_node_id = process_node_id(new_node_id,memory_object,self.nodes,self.statement_interpreter)
                
                
                if new_node_id=="quit":
                    if return_as_dict:
                        return response,memory_object.get_dict()
                    else:
                        return response,memory_object

                else:
                    node = self.nodes[new_node_id]



            """
            execute nodes instruction. This involves getting replies from model and updating the memory object to include the turn. 
            Most nodes have their own apply_instruction function, so behavor will vary by node subclass
            """
            response,new_user_reply,response_to_user=node.apply_instruction(user_reply,memory_object,self.chatbot,self.nodes)



            if not(new_user_reply is None):
      
                user_reply=new_user_reply
            
        if return_as_dict:
            return response,memory_object.get_dict()

        else:
            return response,memory_object
    

    def simulate_user(self,memory_object=None,memory_dict=None,max_turns =40,test_mode=False):
        """
        Function to simulate the user's side of the conversation when running in simulation mode
        Args:
            memory_object - MemoryObject that keeps track of memory of conversation history, states, and variables. Will define memory_object from memory_dict if memory_object isn't defined
            memory_dict - json like dictionary that defines memory object. If both memory_object and memory_dict are undefined, will initialize new memory_object.
            max_turns - used to break out of simulation after certain number of turns
            test_mode - running in test modes mean that all models and APIs will give a default response. Useful for quickly testing random trajectories through graph
        Returns:
            response - string that gives the user's reply
            new_node_id - name of node transition that was sampled to give the user reply
            success - whether call was successful
        """
 
        if memory_object is None:
            
            memory_object = MemoryObject(self.config,memory_dict)

        node = self.nodes[memory_object.get_last_state()]
        ai_replies = memory_object.get_agent_replies()
        human_replies = memory_object.get_user_replies()
  
        inter_node = simulate_interjections(self.nodes,len(ai_replies),max_turns=max_turns)
        self.user_bot.set_test_mode(test_mode)
       
        if inter_node is None:

            new_node_id = node.simulate_transition()
            inputs,outputs,prefix = node.make_user_prompt(ai_replies ,human_replies,memory_object.get_user_prompt(),new_node_id)

            user_instruction = node.user_sims[node.transitions.index(new_node_id)]
        else:
            new_node_id = inter_node
            inputs,outputs,prefix = self.nodes[new_node_id].make_interjection_prompt(ai_replies ,human_replies,memory_object.get_user_prompt())
            user_instruction = self.nodes[new_node_id].user_interjection

        
        if user_instruction==self.config.end_signal:
            return user_instruction,new_node_id,True


        responses,success = self.user_bot(inputs,outputs,prefix)
       

        if success:
            response = post_process_user_responses(responses)
        else:
            response = responses[0]


        return response,new_node_id,success
    
    def apply_fn(self,entry_node,args_list=[],memory_object=None,memory_dict=None,function_type="local",test_mode=False):

        self.test_mode = test_mode
        self.chatbot.set_test_mode(test_mode)
        self.classifier.set_test_mode(test_mode)
        user_reply=""
        if memory_object is None:
            
            #initialize a memory object, empty if not specified
            memory_object = MemoryObject(self.config,memory_dict)

            var_names=[]

            
            for i in range(len(args_list)):
                var_name = "temp_function_arg"+str(i)
                var_names.append(var_name)
                
                #add argument variables to current scope of memory object
                memory_object.set_variable(var_name,args_list[i])
        arg_str = ",".join(var_names)


        function_inst = entry_node[:-1] + arg_str + ")"

        if function_type=="local":
            action = "local_function"
        elif function_type=="global":
            action = "global_function"
        elif function_type=="normal":
            action = "function"
        else:
            raise Exception("function type "+str(function_type) + " invalid")
        

        #add temporary new function node to call function, set only transition to "quit" so that program will terminate when function returns 
        self.add_node(name="temp_function_node",action=action,instruction=function_inst,transitions=["quit"])
        set_state = "temp_function_node"


        #keep iterating until we hit a quit statement, resulting in result to be returned
        while True:
            if not(set_state is None):

                #force next state to be set_state
                new_node_id=set_state
                node = self.nodes[new_node_id]
                set_state=None


            else:
                
                """
                get variable that previous node output
                each node type can have different get_variable_output function, with base behavior defined in BaseNode
                most common is to output the reply from the model or output of a function. Some node types have no/empty variable output
                """
                variable_output = node.get_variable_output(user_reply,memory_object)

                #temporarily assigns variable output to variable 'last_variable_output'. Will also asisgn it to any variables defined in the node's instruction
                memory_object.assign_variables(node,variable_output)




                


                """
                Get the next node id using the nodes transition function. Each node type can have a different apply_transition, with base behavior defined in BaseNod
                if only 1 transition is defined, will usually return this
                if multiple transitions are defined, will use classifier model to answer a multiple choice question defined in the previously executed node to determine new node
                """

                new_node_id = node.apply_transition(user_reply,memory_object,self.classifier,self.nodes,self.config)

                """
                certain node names need additional processing
                for instance "return" transitions go back to the function that called them
                transitions that end in .* implement wildcard transitions for if/else logic
                """
                new_node_id = process_node_id(new_node_id,memory_object,self.nodes,self.statement_interpreter)
                
                if new_node_id=="quit":
                    self.remove_node("temp_function_node")
                    

                    return variable_output

                else:
                    node = self.nodes[new_node_id]



            """
            execute nodes instruction. This involves getting replies from model and updating the memory object to include the turn. 
            Most nodes have their own apply_instruction function, so behavior will vary by node subclass
            """
            response,new_user_reply,response_to_user=node.apply_instruction(user_reply,memory_object,self.chatbot,self.nodes)
            if response_to_user:
                raise Exception("nodes that respond to user (ex: chat nodes) are disabled in function calls from python")



            if not(new_user_reply is None):
      
                user_reply=new_user_reply
            



        

    def add_nodes_from_data_frame(self,df,reset=False):
        """
        Function to add nodes from a dataframe
        Args:
            df - dataframe from spreadsheet
            reset - use to overwrite nodes (instead of add to currently saved nodes)
        """

        if reset:
            self.nodes=OrderedDict()

        if "Name" in df.keys():
            names = df["Name"]
        elif "name" in df.keys():
            names = df["name"]
            
        else:
            raise Exception("must have name in df")

        

        for field in df.keys():

            field_name = field.lower().replace(" ","_")
            if not field_name in self.expected_fields:
                if field[-1]==' ':
                    raise Exception("Field "+str(field)+ " has a trailing space, please delete the trailing space and try again." )
                else:
                    raise Exception("Invalid field "+str(field)+".")
        for i in range(len(names)):
            
            node_fields=dict(zip(self.expected_fields, [None]*len(self.expected_fields)))
            for field in df.keys():
                field_name = field.lower().replace(" ","_")
                node_fields[field_name] = process_cell(df[field][i])

            python_node_fields = df2python(**node_fields)

            self.add_node(**python_node_fields)




                
    def add_node(self,**kwargs):
        """
        Function to add a single node
        Args:
            **kwargs -- args used to initialize a node. See __init__() function for nodes in BaseNode class.
        """
        if "action" in kwargs:
            self.node_args.append(copy.deepcopy(kwargs))
    
            node_class = self.node_types[kwargs['action']]

            

            if "name" in kwargs:
                node = node_class(autogram_config=self.config,statement_interpreter=self.statement_interpreter,**kwargs)
     
                if node.name in self.nodes.keys():
                    raise Exception("Duplicate node name "+str(kwargs['name']))
                

                else:

                    self.nodes[node.name] = node
            else:
                raise Exception("each new node needs a name")


        else:
            raise Exception("each new node needs an action")


    def convert_to_pure_python(self):
        code_str="from autograms import Autogram, AutogramConfig\n\n"
        code_str="#set arguments to AutogramConfig to change settings\nconfig=AutogramConfig()\n\n"
        code_str="#need to load api key dictionary from json file\napi_keys={}"

        code_str+="autogram = Autogram(config=config,api_keys=api_keys,allow_incomplete=True)\n\n\n"
        for item in self.node_args:


            code_str+="#"+item["name"]+ " --> " + ", ".join(item["transitions"])+"\n"
            
            code_str+="autogram.add_node(\n"

            for arg in item.keys():
                if not item[arg] is None:
                    if not item[arg]==[]:
                        code_str+="      "+arg +" = "+repr(item[arg])+",\n"
            code_str+="      " + ")"
            code_str+="\n"




        code_str+="\nautogram.allow_incomplete=False\n"
        code_str+="autogram.update()"

        return code_str


    def convert_to_hybrid_python(self):
        code_str="\n\n"
        for item in self.node_args:


            code_str+="#"+item["name"]+ " --> " + ", ".join(item["transitions"])+"\n"
            
            code_str+="exec_node(\n"

            for arg in item.keys():
                if not item[arg] is None:
                    if not item[arg]==[]:
                        code_str+="      "+arg +" = "+repr(item[arg])+",\n"
            code_str+="      " + ")"
            code_str+="\n"

        return code_str

    def convert_to_df(self):

        all_node_set=set()
        df_node_args=[]
     
        for node_arg in self.node_args:
            item = python2df(**node_arg)
            df_node_args.append(item)
            for arg in item.keys():
                if not item[arg] is None:
                    if not item[arg]==[]:
                        all_node_set.add(arg)
        all_node_set=list(all_node_set)
        all_node_args=[]

        for field in EXPECTED_FIELDS:
            if field in all_node_set:
                all_node_args.append(field)



        
        df = OrderedDict()
        for arg in all_node_args:
            df[arg]=[]

        for item in df_node_args:
            for arg in all_node_args:
                if arg in item and not item[arg] is None and not item[arg]=="":
                     df[arg].append(item[arg])
                else:
                    df[arg].append("")
        return df
    
    def remove_node(self,node_name):
        del self.nodes[node_name]

        for i in range(len(self.node_args)):


            name1=self.node_args[i]['name']
            name2=node_name
            if "(" in name1:
                ind = name1.find("(")
                name1=name1[:ind]
            if "(" in name2:
                ind = name2.find("(")
                name2=name2[:ind]
            
            if name1==name2:
                del self.node_args[i]

                return
            










        


            

        





        






