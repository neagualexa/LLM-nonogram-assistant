import urllib.request
import json
import os
import ssl
from langchain.schema import HumanMessage
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
    content_formatter=LlamaChatContentFormatter(),
)

def callLLM(user_message, past_user_inputs=[], generated_responses=[]):
    
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
        "input_data": [
            user_message
        ],
        "params": {
            "top_p": 0.9,
            "temperature": 0.6,
            "max_new_tokens": 100,
            "do_sample": True,
            "return_full_text": True
        }
    }

    body = str.encode(json.dumps(data))

    url = API_URL
    # Replace this with the primary/secondary key or AMLToken for the endpoint
    api_key = API_KEY
    if not api_key:
        raise Exception("A key should be provided to invoke the endpoint")

    # The azureml-model-deployment header will force the request to go to a specific deployment.
    # Remove this header to have the request observe the endpoint traffic rules
    headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ api_key), 'azureml-model-deployment': MODEL }

    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)

        result = response.read()
        print(result)
        result = json.loads(result)
        return result[0]
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))
    

