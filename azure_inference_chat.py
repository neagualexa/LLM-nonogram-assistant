import urllib.request
import json
from typing import Dict
import azure.LLM_calls.azurecredentials as azurecredentials
from langchain_community.llms.azureml_endpoint import (
    AzureMLOnlineEndpoint,
    ContentFormatterBase
)

'''
HELP: https://python.langchain.com/docs/integrations/chat/azureml_chat_endpoint
'''

API_URL = azurecredentials.api_url
API_KEY = azurecredentials.key

system_message = "You are a helpful assistant replying the user's questions. Reply in short sentences."
# system_message = """You are the Nonogram Solver Assistant. You can help the user tackle nonogram and griddler puzzles with ease. Whether the user is a beginner or an experienced puzzle enthusiast, you are ready to assist them in solving these challenging puzzles. 
#             The user can describe the puzzle or ask for specific tips, and you will guide them through the solving process.
#             You can also engage in some casual talk, like answering greetings and simple questions like "How/Who are you?". 
#             At the beginning of a conversation in your first message, introduce yourself. 
#             Always start with ASSISTANT: when responding to the question.
#             DO NOT COMPLETE THE SENTENCE!
#             ONLY answer the user's questions regarding Nonograms. If you do not know how to answer, reply by saying you do not know. Do not reply to any irrelevant questions."""

class LlamaCustomContentFormatter(ContentFormatterBase):
    """Custom Content formatter for LLaMa 2"""

    def format_request_payload(self, prompt: str, model_kwargs: Dict) -> bytes:
        """Formats the request according to the chosen api"""
        prompt = ContentFormatterBase.escape_special_characters(prompt)
        # print("prompt:: ", prompt)
        # print("history:: ", model_kwargs.get("history"))
        request_payload = json.dumps(
            {
                "messages": [
                    # comment system message and history if using langchain
                    {"role": "system", "content": system_message},         # langchain does the system message magic
                    *model_kwargs.get("history"),                          # langchain does the memory magic
                    {"role": "user", "content": prompt}                    # langchain adds the history into the prompt with System, AI, Human labels
                ],
                "temperature": model_kwargs.get("temperature"),             # can add default value here
                "max_tokens": model_kwargs.get("max_tokens"),
            }
        )
        print("request_payload:: ", request_payload)
        return str.encode(request_payload)

    def format_response_payload(self, output: bytes) -> str:
        """Formats response"""
        print("output:: ", output)
        return json.loads(output)["choices"][0]["message"]["content"]
    
# NOTES:
# conversation memory can be done through adding multiple messages (make sure JSON is correct, so comma at end)  -> memory preserved as we fetch it from DB
# OR through adding the conversation into the prompt (as langchaind does it) -> memory lost at every app restart

content_formatter = LlamaCustomContentFormatter()

llm = AzureMLOnlineEndpoint(
    endpoint_url=API_URL,
    endpoint_api_type="serverless",
    endpoint_api_key=API_KEY,
    content_formatter=content_formatter,
    model_kwargs={"temperature": 0.8, "max_tokens": 50, "history": []},
)

def callLLM(user_message, past_messages=[]):
    
    try:
        llm.model_kwargs["history"] = past_messages
        response = llm.invoke(input=user_message) # [HumanMessage(content=user_message)], config=metadata
        print("response:: ", response)
        return response
        # return "test response"
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))
    

