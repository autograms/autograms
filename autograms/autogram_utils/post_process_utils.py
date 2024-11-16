from ..program_control import GoTo, ReturnTo




def process_node_id(new_node_id):
    
    

    if new_node_id[:len("returnto")]=="returnto":
        return_dest = new_node_id.split(" ")[0]
        return ReturnTo(destination = return_dest)
    else:
        return GoTo(new_node_id)
    

    pass


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