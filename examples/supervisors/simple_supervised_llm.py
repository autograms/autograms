
from autograms.functional import call_llm



def fixed_target(target):
    return target


@autograms_function()
def chatbot(target):
    last_input = get_last_user_reply()
    result = call_llm(last_input,supervisor=fixed_target,supervisor_kwargs={"target":target})
    return result