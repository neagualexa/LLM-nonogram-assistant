import urllib.request
import json
import os
from typing import Dict
import azure.LLM_calls.azurecredentials as azurecredentials
from langchain.schema import HumanMessage, AIMessage
# from langchain_community.chat_models.azureml_endpoint import (
#     AzureMLChatOnlineEndpoint,
#     LlamaContentFormatter,
# )
from langchain_community.llms.azureml_endpoint import (
    AzureMLOnlineEndpoint,
    LlamaContentFormatter,
    ContentFormatterBase
)

'''
HELP: https://python.langchain.com/docs/integrations/chat/azureml_chat_endpoint
'''

API_URL = azurecredentials.api_url
API_KEY = azurecredentials.key

class CustomFormatter(ContentFormatterBase):
    content_type = "application/json"
    accepts = "application/json"

    def format_request_payload(self, prompt: str, model_kwargs: Dict) -> bytes:
        input_str = json.dumps(
            {
                "inputs": [prompt],
                "parameters": model_kwargs,
                "options": {"use_cache": False, "wait_for_model": True},
            }
        )
        return str.encode(input_str)

    def format_response_payload(self, output: bytes) -> str:
        response_json = json.loads(output)
        return response_json[0]["summary_text"]

content_formatter = CustomFormatter()

llm = AzureMLOnlineEndpoint(
    endpoint_url=API_URL,
    endpoint_api_type="serverless",
    endpoint_api_key=API_KEY,
    content_formatter=content_formatter,
    model_kwargs={"temperature": 0.8},
)

def callLLM(user_message, past_user_inputs=[], generated_responses=[]):
    
    try:
        response = llm.invoke(user_message)
        print(response)
        result = response[0].content
        return result
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))
    

