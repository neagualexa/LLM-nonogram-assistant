
API_TOKEN = "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"

import requests
import time
headers = {"Authorization": f"Bearer {API_TOKEN}"}

# ####### LIMITED TO ONLY 25 TOKENS PER RESPONSE! VERY SHORT #######
# https://huggingface.co/docs/api-inference/detailed_parameters#summarization-task

# Conversational
API_URL_CONV = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
API_URL_CONV = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
# Question Answering
API_URL_QA = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
# Summarization
API_URL_SUM = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
# Text Generation
API_URL_TEXTGEN = "https://api-inference.huggingface.co/models/openai-community/openai-gpt"
# Text2Text Generation
API_URL_TEXT2TEXT = "https://api-inference.huggingface.co/models/MBZUAI/LaMini-Flan-T5-783M"

tasks = ["conversational", "question-answering", "summarization", "text-generation", "text2text-generation"]
TASK = tasks[0]

def query(user_message, past_user_inputs=[], generated_responses=[]):
    
    start_time = time.time()
    response = {}
    if TASK == "conversational":
        # for Conversational dialoGPT
        payload = {
            "inputs": {
                "past_user_inputs": past_user_inputs,
                "generated_responses": generated_responses,
                "text": user_message
            }
        }
        response = requests.post(API_URL_CONV, headers=headers, json=payload)    
    elif TASK == "question-answering":
        # for Question Answering roberta-base-squad2
        payload = {
            "inputs": {
                "question": user_message,
                "context": "My name is Clara and I live in Berkeley.",
            }
        }
        response = requests.post(API_URL_QA, headers=headers, json=payload)   
    elif TASK == "summarization":
        # for Summarization bart-large-cnn
        payload = {
            "inputs": [user_message, "The tower is 324 metres (1,063 ft) tall, about the same height as an 81-storey building, and the tallest structure in Paris. Its base is square, measuring 125 metres (410 ft) on each side. During its construction, the Eiffel Tower surpassed the Washington Monument to become the tallest man-made structure in the world, a title it held for 41 years until the Chrysler Building in New York City was finished in 1930. It was the first structure to reach a height of 300 metres. Due to the addition of a broadcasting aerial at the top of the tower in 1957, it is now taller than the Chrysler Building by 5.2 metres (17 ft). Excluding transmitters, the Eiffel Tower is the second tallest free-standing structure in France after the Millau Viaduct."],
            "parameters": {"do_sample": False},
        }
        response = requests.post(API_URL_SUM, headers=headers, json=payload)
    elif TASK == "text-generation":
        # for Text Generation openai-gpt
        payload = {
            "inputs": user_message
        }
        response = requests.post(API_URL_TEXTGEN, headers=headers, json=payload)
    elif TASK == "text2text-generation":
        # for Text2Text Generation LaMini-Flan-T5-783M
        payload = {
            "inputs": user_message
        }
        response = requests.post(API_URL_TEXT2TEXT, headers=headers, json=payload)
    
    end_time = time.time()
    latency = end_time - start_time
    print(f"Latency: {latency} seconds")
    result = response.json()
    
    print(result)
    
    if TASK == "conversational":
        # for conversational dialoGPT
        return result['generated_text']
    elif TASK == "question-answering":
        # for Question Answering roberta-base-squad2
        return result['answer']
    elif TASK == "summarization":
        # for Summarization bart-large-cnn
        return result[0]['summary_text']
    elif TASK == "text-generation":
        # for Text Generation openai-gpt
        return result[0]['generated_text']
    elif TASK == "text2text-generation":
        # for Text2Text Generation LaMini-Flan-T5-783M
        return result[0]['generated_text']
    
    return result

# data = query(
#     {
#         "inputs": {
#             "past_user_inputs": ["Which movie is the best ?"],
#             "generated_responses": ["It's Die Hard for sure."],
#             "text": "Can you explain why ?",
#         },
#     }
# )
# print(data)
