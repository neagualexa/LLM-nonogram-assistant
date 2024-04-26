import requests
import time
import urllib.error
import azure.LLM_calls.azurecredentials as azurecredentials


API_TOKEN = azurecredentials.hf_api_token
headers = {"Authorization": f"Bearer {API_TOKEN}"}
# API_URL_TEXTGEN = "https://api-inference.huggingface.co/models/MBZUAI/LaMini-Flan-T5-783M"
API_URL_TEXTGEN = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"

meaning_system_message = "Under Answer section, write 'true' if the user guess is a synonym or describes something similar to the Solution; otherwise, return 'false'.  Do not return an explanation.\n"

def meaning_checker_hf(user_message, solution):
    # if user_message.lower() == solution.lower():
    #     return "true", 0
    if user_message == "" or user_message == "Enter...": # should never be reached as this check is done in Unity
        return "false", -1
    message = f"""User guess: {user_message} \nSolution: {solution} \nAnswer:"""
    context = meaning_system_message + message

    start_time = time.time() 
    payload = {
            "inputs": context,
            "parameters": {
                "return_full_text": False
            }
        }
    response = requests.post(API_URL_TEXTGEN, headers=headers, json=payload)
        
    end_time = time.time()
    latency = end_time - start_time
    print(f"Latency: {latency} seconds")
    result = response.json()
    
    if 'error' in result:
        print("error:: ", result)
        return "HF error", -1
    # print(result)
    result = filter_crop_llm_response(result[0]['generated_text'].lower())
    print(result)
    return result, latency

# API_URL_TEXTGEN = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
API_URL_TEXTGEN = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"

def component_pipeline_query_hf(system_prompt, max_new_tokens):

    context = system_prompt

    start_time = time.time() 
    payload = {
            "inputs": context,
            "use_cache": False,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "return_full_text": False, #  for mistral If set to False, the return results will not contain the original query making it easier for prompting.
                "temperature": 0.2,
                "top_p": 0.7,
                "top_k": 90,
            }
        }
    response = requests.post(API_URL_TEXTGEN, headers=headers, json=payload)
        
    end_time = time.time()
    latency = end_time - start_time
    print(f"Latency: {latency} seconds")
    result = response.json()
    
    # print(result)
    if 'error' in result:
        print("error:: ", result)
        return "HF error", -1
    return result[0]['generated_text'], latency

def filter_crop_llm_response(response):
    # only accept the sentence between the first ':' and '\n' 
    response = response.split("\n")[0]
    if ("'" in response):
        if (response[-1] == "'"):
            response = response[:-1]
    return response

if __name__ == "__main__":
    user_message = "brown drink"
    solution = "coffee"
    response, _ = meaning_checker_hf(user_message, solution)
    print("response:: ", response)
    
  
  
# AZURE ENDPOINT  
    
# import urllib.request
# import json
# import os
# from typing import Dict
# import azure.LLM_calls.azurecredentials as azurecredentials
# from langchain.schema import HumanMessage, AIMessage
# from langchain_community.llms.azureml_endpoint import (
#     AzureMLOnlineEndpoint,
#     LlamaContentFormatter,
#     ContentFormatterBase
# )

# '''
# HELP: https://python.langchain.com/docs/integrations/chat/azureml_chat_endpoint
# '''

# API_URL = azurecredentials.api_url
# API_KEY = azurecredentials.key
# solution = "coffee cup"

# system_message = "Return 'true' if the user's guess is a synonym or describes something similar to the solution; otherwise, return 'false'."

# class LlamaCustomContentFormatter(ContentFormatterBase):
#     """Custom Content formatter for LLaMa 2"""

#     def format_request_payload(self, prompt: str, model_kwargs: Dict) -> bytes:
#         """Formats the request according to the chosen api"""
#         prompt = ContentFormatterBase.escape_special_characters(prompt)
#         print("prompt:: ", prompt)
#         request_payload = json.dumps(
#             {
#                 "messages": [
#                     {"role": "system", "content": system_message},
#                     {"role": "user", "content": prompt}
#                 ],
#                 "temperature": model_kwargs.get("temperature"), # can add default value here
#                 "max_tokens": model_kwargs.get("max_tokens"),
#             }
#         )
#         print("request_payload:: ", request_payload)
#         return str.encode(request_payload)

#     def format_response_payload(self, output: bytes) -> str:
#         """Formats response"""
#         print("output:: ", output)
#         return json.loads(output)["choices"][0]["message"]["content"]

# content_formatter = LlamaCustomContentFormatter()

# llm = AzureMLOnlineEndpoint(
#     endpoint_url=API_URL,
#     endpoint_api_type="serverless",
#     endpoint_api_key=API_KEY,
#     content_formatter=content_formatter,
#     model_kwargs={"temperature": 1, "max_tokens": 2, "history": []},
# )

# def callLLM_checker(user_message):
    
#     try:
#         message = f"""User guess: {user_message}
# Solution: {solution}"""
#         response = llm.invoke(input=message)
#         print("response:: ", response)
#         return response
#         # return "test response"
#     except urllib.error.HTTPError as error:
#         print("The request failed with status code: " + str(error.code))

#         # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
#         print(error.info())
#         print(error.read().decode("utf8", 'ignore'))
    

# if __name__ == "__main__":
#     user_message = "dog"
#     response = callLLM_checker(user_message)