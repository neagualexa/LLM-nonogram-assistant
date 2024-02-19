import urllib.request
import json
import os
import ssl
from azure.LLM_calls import azurecredentials
from langchain.schema import HumanMessage
from langchain_community.llms.azureml_endpoint import (
    AzureMLOnlineEndpoint,
    LlamaContentFormatter,
    ContentFormatterBase
)

'''
HELP: https://python.langchain.com/docs/integrations/chat/azureml_chat_endpoint
'''

MODEL =  'Llama-2-7b-chat'
API_URL = azurecredentials.api_url
API_KEY = azurecredentials.key

def callLLM(user_message, past_user_inputs=[], generated_responses=[]):
    
    print("Azure inference call...")
    
    def allowSelfSignedHttps(allowed):
        # bypass the server certificate verification on client side
        if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
            ssl._create_default_https_context = ssl._create_unverified_context

    allowSelfSignedHttps(True) # this line is needed if you use self-signed certificate in your scoring service.

    # Request data goes here
    # The example below assumes JSON formatting which may be updated
    # depending on the format your endpoint expects.
    # More information can be found here:
    # https://docs.microsoft.com/azure/machine-learning/how-to-deploy-advanced-entry-script
    data = {
        "messages":
        [
            { 
            "role": "user", 
            "content": user_message},
        ],
        "temperature": 0.8,
        "max_tokens": 50,
    }

    body = str.encode(json.dumps(data))

    url = API_URL
    # Replace this with the primary/secondary key or AMLToken for the endpoint
    api_key = API_KEY
    if not api_key:
        raise Exception("A key should be provided to invoke the endpoint")

    # The azureml-model-deployment header will force the request to go to a specific deployment.
    # Remove this header to have the request observe the endpoint traffic rules
    headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ api_key) }

    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)

        result = response.read()
        print(result)
        result = json.loads(result)
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))
    

