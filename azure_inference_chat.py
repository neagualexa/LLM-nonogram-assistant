import urllib.request
import json
import os
import ssl
from langchain.schema import HumanMessage, AIMessage
from langchain_community.chat_models.azureml_endpoint import (
    AzureMLChatOnlineEndpoint,
    LlamaChatContentFormatter,
)

'''
HELP: https://python.langchain.com/docs/integrations/chat/azureml_chat_endpoint
'''

API_URL = "https://ml-workpace2-ulhqe.eastus2.inference.ml.azure.com/score"
MODEL =  'msft-orca-2-7b-2'
API_KEY = "jcac74j9Yd8MHjlCmdrP9f3XPo4eiXhh"

chat = AzureMLChatOnlineEndpoint(
    endpoint_url=API_URL,
    endpoint_api_type=AzureMLChatOnlineEndpoint.AzureMLEndpointApiType.realtime,
    endpoint_api_key=API_KEY,
    content_formatter=LlamaChatContentFormatter,
    model_kwargs={"temperature": 0.8},
)

def callLLM(user_message, past_user_inputs=[], generated_responses=[]):
    
    try:
        response = chat.invoke(
            [HumanMessage(content=user_message)],
            max_tokens=512,
        )
        print(response)
        result = response[0].content
        return result
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))
    

