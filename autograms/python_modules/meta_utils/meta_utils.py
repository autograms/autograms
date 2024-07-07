import string


#checks if name is a all lowercase and underscore
def check_node_name(name):
    
    if not(name[0]).lower() in string.ascii_lowercase:
        return False
    
    for i in range(1,len(name)):
        if not(name[i]).lower() in string.ascii_lowercase + "_":
            return False
        
    return True
