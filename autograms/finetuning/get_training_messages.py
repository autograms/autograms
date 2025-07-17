from autograms import AutogramConfig, use_config
import autograms
import json


def get_training_messages(memory_list,autogram_config,train_chatbot=True,train_structured=True,train_classifier = True,score_threshold=None,require_score=False,require_supervisor=True,tag_query=None):


    preprocess_func =autograms.apis.openai_models.get_chatbot_messages
    classifier_preprocess_func =autograms.apis.openai_models.get_classifier_messages
    
    all_train = []

    for memory_dict in memory_list:
        for turn in memory_dict['model_turns']:
            if turn['entry_type']=="model":


                if require_supervisor:
                    if (not "supervisor_info" in turn):
                        continue
                    if turn["supervisor_info"] is None:
                        continue
                
                if score_threshold or require_score:
                    meta_info = turn["supervisor_info"]
                    if meta_info is None:
                        continue
                    if require_score:
                        if not 'score' in meta_info or (meta_info['score'] is None):
                            continue
                    if score_threshold:
                        if 'score' in meta_info and (meta_info['score'] < score_threshold):
                            continue

                if not tag_query is None and len(tag_query)>0:
                    
                    tags = turn["supervisor_info"]['tags']
                    if tags is None:
                        continue
                    print(tags)
                    if not meets_condition(tag_query,tags):
                        continue
                    # if tags is None:
                    #     continue
                    # tags_present = True
                    # for tag in required_tags:
                    #     if not tag in tags:
                    #         tags_present = False
                    # if not tags_present:
                    #     continue
                if turn['function_name']=='call_classifier' and train_classifier:
                    with use_config(autogram_config):
                        messages = preprocess_func(turn["function_inputs"]["input_turns"],turn["function_inputs"]["output_turns"],turn["function_inputs"]["system_prompt"],multi_modal_inputs =turn["function_inputs"]["multi_modal_inputs"])
                if turn['function_name']=='call_model' and train_chatbot:
                    with use_config(autogram_config):
                        messages= classifier_preprocess_func(turn["function_inputs"]["input_turns"],turn["function_inputs"]["output_turns"],turn["function_inputs"]["system_prompt"],multi_modal_inputs =turn["function_inputs"]["multi_modal_inputs"] )
                if turn['function_name']=='call_object_model' and train_structured:
                    with use_config(autogram_config):
                        messages = preprocess_func(turn["function_inputs"]["input_turns"],turn["function_inputs"]["output_turns"],turn["function_inputs"]["system_prompt"],multi_modal_inputs =turn["function_inputs"]["multi_modal_inputs"])
                if turn['function_name'] == "call_chat_completion" and train_chatbot:
                    messages = turn["function_inputs"]["messages"]
                if turn['function_name'] == "call_completion" and train_chatbot:
                    messages=[{"role":"user","content":turn["function_inputs"]["prompt"]}]
           
                for message in messages:
                    if message["role"]=="assistant":
                        message["weight"]=0
                if type(turn['output'])==list:
                    messages.append({"role":"assistant","content":[{"type": "text", "text":turn['output'][0]}],"weight":1})
                else:
                    messages.append({"role":"assistant","content":[{"type": "text", "text":turn['output']}],"weight":1})


                message_dict = {"messages":messages}
         

                all_train.append(message_dict)

    return all_train
def get_training_messages_dpo(
    memory_list,
    autogram_config,
    train_chatbot=True,
    train_structured=True,
    train_classifier=True,
    score_threshold=None,
    require_score=False
):
    """
    Convert memory_list entries into an OpenAI DPO fine-tuning format.
    If meta_info['rejected'] exists, it populates non_preferred_output.
    """

    preprocess_func = autograms.apis.openai_models.get_chatbot_messages
    classifier_preprocess_func = autograms.apis.openai_models.get_classifier_messages

    all_train = []

    for memory_dict in memory_list:
        for turn in memory_dict["model_turns"]:
            # We only process model turns
            if turn['entry_type'] != "model":
                continue

            if (not "supervisor_info" in turn):
                continue
            
            if turn["supervisor_info"] is None:
                continue
      
            # Score filters
            meta_info = turn.get("supervisor_info", {})
            if meta_info is None:
                continue

            if require_score:
                # Skip if no score or None
                if 'score' not in meta_info or meta_info['score'] is None:
                    continue
            if score_threshold is not None:
                # Skip if score < threshold
                if meta_info.get('score', float('-inf')) < score_threshold:
                    continue

            # Select which preprocessing function to use
            # (Based on function_name and train_* flags)
            messages = []
            fn_name = turn.get('function_name')
            if fn_name == 'call_classifier' and train_classifier:
                with use_config(autogram_config):
                    messages = classifier_preprocess_func(
                        turn["function_inputs"]["input_turns"],
                        turn["function_inputs"]["output_turns"],
                        turn["function_inputs"]["system_prompt"],
                        multi_modal_inputs=turn["function_inputs"].get("multi_modal_inputs", [])
                    )
            elif fn_name == 'call_model' and train_chatbot:
                with use_config(autogram_config):
                    messages = preprocess_func(
                        turn["function_inputs"]["input_turns"],
                        turn["function_inputs"]["output_turns"],
                        turn["function_inputs"]["system_prompt"],
                        multi_modal_inputs=turn["function_inputs"].get("multi_modal_inputs", [])
                    )
            elif fn_name == 'call_object_model' and train_structured:
                with use_config(autogram_config):
                    messages = preprocess_func(
                        turn["function_inputs"]["input_turns"],
                        turn["function_inputs"]["output_turns"],
                        turn["function_inputs"]["system_prompt"],
                        multi_modal_inputs=turn["function_inputs"].get("multi_modal_inputs", [])
                    )
            elif fn_name == "call_chat_completion" and train_chatbot:
                messages = turn["function_inputs"]["messages"]
            elif fn_name == "call_completion" and train_chatbot:
                messages=[{"role":"user","content":turn["function_inputs"]["prompt"]}]
            else:
                # If it doesn't match any of the above training modes, skip
                continue

            # Build the DPO format:
            # 1) "input" block with the conversation messages and any optional tool usage
            # 2) "preferred_output" block with the chosen (accepted) assistant reply
            # 3) "non_preferred_output" block with any rejected reply (if meta_info['rejected'])
            convert_message_list(messages)
            dpo_input = {
                "messages": messages,     # <== all user/system messages so far
            }

            # The final "accepted" output (preferred)
            if type(turn['output'])==list:
                preferred_output = [
                    {
                        "role": "assistant",
                        # If your turn['output'] is a list of strings, pick the first or join them
                        "content": turn['output'][0] if turn['output'] else ""
                    }
                ]
            else:
                preferred_output = [
                    {
                        "role": "assistant",
                        # If your turn['output'] is a list of strings, pick the first or join them
                        "content": turn['output'] if turn['output'] else ""
                    }
                ]


            # Handle rejected outputs (if any)
            # meta_info['rejected'] could be a single string or a list of strings
            non_preferred_output = []
            rejected_content = meta_info.get('rejected_output')
            if rejected_content:
                if isinstance(rejected_content, list):
                    for r in rejected_content:
                        non_preferred_output.append({
                            "role": "assistant",
                            "content": r
                        })
                else:
                    non_preferred_output.append({
                        "role": "assistant",
                        "content": rejected_content
                    })

            if len(non_preferred_output)==0:
                continue

            # Create the final training dictionary
            training_dict = {
                "input": dpo_input,
                "preferred_output": preferred_output,
                "non_preferred_output": non_preferred_output
            }

            all_train.append(training_dict)
   
    return all_train


    
def convert_messages(messages_list,remove_weight=False):

    for messages in messages_list:
        convert_message_list(messages['messages'],remove_weight=remove_weight)
        # for message in messages['messages']:
        #     if type(message['content'])==list:
        #         message['content'] = message['content'][0]['text']
        #     if remove_weight:
        #         if "weight" in message:
        #             del message["weight"]



def convert_message_list(messages,remove_weight=False):


    for message in messages:
        if type(message['content'])==list:
            message['content'] = message['content'][0]['text']
        if remove_weight:
            if "weight" in message:
                del message["weight"]


def meets_condition(query, tags):
    """
    Evaluate whether the boolean expression `query` is satisfied by the given list of `tags`.
    Operators: & (AND), | (OR)
    Parentheses allowed for grouping.
    Left-to-right evaluation unless parentheses override.
    """
    
    # 1. Tokenize the query.
    tokens = tokenize(query)
    
    # 2. Parse (and evaluate) the tokens to get a boolean result.
    #    We define a small recursive-descent parser that:
    #    - parse_expr: parses a sequence of factors (operands) separated by & or | (left to right).
    #    - parse_factor: either a parenthesized expression or a single string check.
    #
    #    Because we parse left-to-right for both & and | (same precedence),
    #    parse_expr repeatedly reads factors + operators in sequence.
    #
    #    The final result is True/False.
    
    # We'll use an iterator over tokens so our parse functions can consume them in order.
    it = TokenIterator(tokens)
    result = parse_expr(it, tags)
    
    # If there are leftover tokens, there's probably a syntax issue in the query;
    # you can decide how strictly you want to handle errors.
    if not it.is_finished():
        raise ValueError("Unexpected extra tokens in query.")
    
    return result


def tokenize(query_string):
    """
    Converts the query string into a list of tokens: parentheses '(', ')',
    operators '&', '|', and strings (operands).
    """
    tokens = []
    i = 0
    n = len(query_string)
    while i < n:
        c = query_string[i]
        
        # Skip whitespace
        if c.isspace():
            i += 1
            continue
        
        # Single-character tokens: operators and parentheses
        if c in ('&', '|', '(', ')'):
            tokens.append(c)
            i += 1
        else:
            # Accumulate characters for a "tag" (operand)
            start = i
            while i < n and query_string[i] not in ('&', '|', '(', ')'):
                i += 1
            # The substring [start:i] is the operand (strip whitespace just in case).
            operand = query_string[start:i].strip()
            if operand:
                tokens.append(operand)
    
    return tokens


class TokenIterator:
    """
    A small helper to advance through the list of tokens.
    """
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
    
    def current_token(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None  # no more tokens
    
    def next_token(self):
        # Return the current token and advance the position by 1
        tok = self.current_token()
        self.position += 1
        return tok
    
    def peek(self):
        # Look at the current token without consuming it
        return self.current_token()
    
    def is_finished(self):
        return self.position >= len(self.tokens)


def parse_expr(it, tags):
    """
    Parse an expression of the form:
      factor ( & factor | | factor )*
    evaluating left-to-right.
    """
    # First factor
    value = parse_factor(it, tags)
    
    # Repeatedly look for operators & or |, read the next factor, combine.
    while True:
        op = it.peek()
        if op == '&':
            it.next_token()  # consume '&'
            right_val = parse_factor(it, tags)
            value = value and right_val
        elif op == '|':
            it.next_token()  # consume '|'
            right_val = parse_factor(it, tags)
            value = value or right_val
        else:
            break  # no more operators at this level
    return value


def parse_factor(it, tags):
    """
    A factor is either:
      - '(' expr ')'
      - a single string operand (checked for membership in `tags`)
    """
    tok = it.peek()
    if tok == '(':
        it.next_token()  # consume '('
        value = parse_expr(it, tags)
        closing = it.next_token()  # should be ')'
        if closing != ')':
            raise ValueError("Missing closing parenthesis.")
        return value
    else:
        # It's presumably a string operand
        operand = it.next_token()
        # Return True/False whether this operand is in tags
        return (operand in tags)