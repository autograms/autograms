import json
from autograms import Autogram, AutogramConfig, use_config, load_autogram, autograms_function
from autograms.functional import set_system_prompt,reply_instruction, reply, generate_list


import pandas as pd
import argparse
import os
import random

@autograms_function()
def userbot_deterministic(message):

    
    while True:

        reply(message)


@autograms_function()
def userbot_simple(prompt="You are testing a chatbot. Try asking it different questions. Each reply should ask a question",instruction="Ask the model a new question."):
    set_system_prompt(prompt)
    
    while True:

        reply_instruction(instruction)



@autograms_function()
def userbot_variable(prompt="You are testing a chatbot. Try asking it different questions. Each reply should ask a question",instruction="Ask the model a new question."):
    set_system_prompt(prompt)
    
    while True:

        list_replies = generate_list(f"generate a list of replies in the conversation that obey this {instruction}")
        if len(list_replies)>0:
            chosen = random.choice(list_replies)
            reply(chosen)
        else:
            reply_instruction(instruction)



class ChatbotSimulator():
    def __init__(self,autogram,user_autogram):
        self.autogram = autogram
        self.user_autogram=user_autogram


    def simulate(self,num_turns=1,chatbot_kwargs={},user_kwargs={},user_memory=None,chatbot_memory=None,user_goes_first=False):
        if not user_goes_first:
            chat_reply, chatbot_memory = self.autogram.reply(None, memory_object=chatbot_memory,**chatbot_kwargs)
        else:
            chat_reply=None
        for i in range(num_turns):
            user_reply, user_memory = self.user_autogram.reply(chat_reply, memory_object=user_memory,**user_kwargs)

            chat_reply, chatbot_memory = self.autogram.reply(user_reply, memory_object=chatbot_memory,**chatbot_kwargs)
        

        return chatbot_memory,user_memory
    

