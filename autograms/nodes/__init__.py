


#from .nodes import FunctionNode,LocalFunctionNode,GlobalFunctionNode,TransitionNode,ChatNode,ChatExactNode,ChatSuffixNode,SetPromptNode,AppendPromptNode,SetUserPromptNode,AppendUserPromptNode,ThoughtNode,ThoughtExactNode,ThoughtQANode
print("loading nodes")
from .base_node import BaseNode, EXPECTED_FIELDS
from .thought_nodes import ThoughtNode,ThoughtExactNode,ThoughtQANode
from .function_nodes import FunctionNode,LocalFunctionNode,GlobalFunctionNode
from .transition_nodes import TransitionNode
from .chat_nodes import ChatNode,ChatExactNode,ChatSuffixNode
from .prompt_nodes import SetPromptNode,AppendPromptNode,SetUserPromptNode,AppendUserPromptNode
from .python_nodes import PythonFunctionNode





NODE_TYPES={"function":FunctionNode,"local_function":LocalFunctionNode,"global_function":GlobalFunctionNode,"transition":TransitionNode,"chat":ChatNode,"chat_exact":ChatExactNode,"chat_suffix":ChatSuffixNode,"set_prompt":SetPromptNode,"append_prompt":AppendPromptNode,"set_user_prompt":SetUserPromptNode,"append_user_prompt":AppendUserPromptNode,"thought":ThoughtNode,"thought_exact":ThoughtExactNode,"thought_qa":ThoughtQANode,"python_function":PythonFunctionNode}