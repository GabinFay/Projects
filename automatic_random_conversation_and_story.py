#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 17:43:39 2024

@author: gabinfay
"""

from openai import OpenAI, RateLimitError
import os
import json
import time

client = OpenAI()

# Add the new function for retrying API calls
def create_chat_completion_with_retry(model, messages, max_retries=5, initial_wait=1):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(model=model, messages=messages)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = initial_wait * (2 ** attempt)
            print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

#%%

scenario_generator_agent = [{"role": "system", "content":"""Your goal is to help the user create a scenario of two people having a conversation. You will create the location, time, and mood of the place where the conversation happens. You will also generate the personalities of the two persons having a conversation. You will decide the level of their English, and write a medium-length description of each person. Write the personality description in the style: 'You are this person. These are your personality traits and you must act like this ...' kind of style. 
                             Mention in the person description that their replies should be rather small. No more than 20 words.
                                                     Also, make sure that their personalities are really different, to offer a rich unusual conversation.
                                                     Then, you will also write the first message of the conversation. No more than 20 words.
                                                     The person1 is the first person to talk.
                                                     You will return this in json format with the following keys: {'scenario', 'person1_personality', 'person2_personality',  'person1_first_message'}.
                                                     But just return a string, don't add a json string tag at the beginning.
                                                     Everything should be created so that the result is clever, smart, funny, and absurd.
                                                     But one of the characters might be dumb, or not."""}]

# Use the new function instead of direct API call
completion = create_chat_completion_with_retry("gpt-4o-mini", scenario_generator_agent)

json_str = completion.choices[0].message.content

#%% Parse generated scenario and personalities

dict_obj = json.loads(json_str)
scenario = dict_obj['scenario']
person1_personality = dict_obj['person1_personality']
person2_personality = dict_obj['person2_personality']
person1_first_message = dict_obj['person1_first_message']


#%%

conversation_setup_1 = [{"role": "system", "content": person1_personality}]
conversation_setup_2 = [{"role": "system", "content": person2_personality}]

conversation_history_1 = conversation_setup_1 + [{"role": "assistant", "content": person1_first_message}]
conversation_history_2 = conversation_setup_2 + [{"role": "user", "content": person1_first_message}]

#%% Conversation loop

num_messages = 50
conversation_memory = [f"Bob: {person1_first_message}"]

#%%

scenario_modifier_agent = [{"role": "system",
    "content":f"""This is a conversation between Alice and Bob in a given place. Your goal is to introduce an event, a modification of their environment, so that their conversation and what they should do will change. You must introduce a perturbator element to it. The perturbator element should be linked to the latest things in the conversation.
    Scenario: {scenario},
    Conversation: {conversation_memory[-2:]}.
    You will return a string that describes what new thing is happening in the scenario, but you won't redescribe the whole scenario."""}]


for i in range(num_messages - 1):
    if i % 5 == 0 and i != 0:  # Introduce scenario change every 5 turns
        conversation_history_1 = conversation_setup_1 + conversation_history_1[-2:]
        conversation_history_2 = conversation_setup_2 + conversation_history_2[-2:]
        
        # Use the new function for scenario modification
        new_scenario = create_chat_completion_with_retry("gpt-4o-mini", scenario_modifier_agent)
        scenario += new_scenario.choices[0].message.content
    
    # Alice's reply
    completion = create_chat_completion_with_retry("gpt-4o-mini", conversation_history_2)
    alice_reply = completion.choices[0].message.content
    print(f"Alice's reply: {alice_reply}")
    print('########################################################################\n#########################################################################')
    conversation_history_1.append({"role": "user", "content": alice_reply})
    conversation_history_2.append({"role": "assistant", "content": alice_reply})
    conversation_memory.append(f"Alice: {alice_reply}")
        
    # Bob's reply
    completion = create_chat_completion_with_retry("gpt-4o-mini", conversation_history_1)
    bob_reply = completion.choices[0].message.content
    print(f"Bob's reply: {bob_reply}")
    print('########################################################################\n#########################################################################')
    conversation_history_1.append({"role": "assistant", "content": bob_reply})
    conversation_history_2.append({"role": "user", "content": bob_reply})
    conversation_memory.append(f"Bob: {bob_reply}")
