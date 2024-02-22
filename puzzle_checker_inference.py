import requests
import time
import azure.LLM_calls.azurecredentials as azurecredentials

API_TOKEN = azurecredentials.hf_api_token
headers = {"Authorization": f"Bearer {API_TOKEN}"}
API_URL_TEXTGEN = "https://api-inference.huggingface.co/models/MBZUAI/LaMini-Flan-T5-783M"

system_message = "Under Answer section, write 'true' if the user guess is a synonym or describes something similar to the Solution; otherwise, return 'false'. \n"

def query_checker_hf(user_message, solution):
    message = f"""User guess: {user_message} \nSolution: {solution} \nAnswer:"""
    context = system_message + message

    start_time = time.time() 
    payload = {
            "inputs": context
        }
    response = requests.post(API_URL_TEXTGEN, headers=headers, json=payload)
        
    end_time = time.time()
    latency = end_time - start_time
    print(f"Latency: {latency} seconds")
    result = response.json()
    
    print(result)
    return result[0]['generated_text']

if __name__ == "__main__":
    user_message = "brown drink"
    solution = "coffee"
    response = query_checker_hf(user_message, solution)
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