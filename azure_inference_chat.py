import urllib.request
import json
import time
from typing import Dict
import azure.LLM_calls.azurecredentials as azurecredentials
from langchain_community.llms.azureml_endpoint import (
    AzureMLOnlineEndpoint,
    ContentFormatterBase
)
from system_prompt import system_prompt, system_prompt_positioning, system_prompt_observe_around, system_prompt_hint
from grid_difference_checker import reformat_cellStates, compare_grids, generate_mistake_markers, print_format_cellStates, random_element, describe_point_position
from puzzle_checker_inference import component_pipeline_query_hf
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
                    {"role": "system", "content": model_kwargs.get("system_message")},         # langchain does the system message magic
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
# OR through adding the conversation into the prompt (as langchain does it) -> memory lost at every app restart

content_formatter = LlamaCustomContentFormatter()

llm = AzureMLOnlineEndpoint(
    endpoint_url=API_URL,
    endpoint_api_type="serverless",
    endpoint_api_key=API_KEY,
    content_formatter=content_formatter,
    model_kwargs={"temperature": 0.8, "max_tokens": 50, "history": [], "system_message": ""},
)

################ Function call for chat message conversation ################

def callLLM(user_message, past_messages=[]):
    
    try:
        llm.model_kwargs["history"] = past_messages
        llm.model_kwargs["system_message"] = system_message
        # response = llm.invoke(input=user_message) # [HumanMessage(content=user_message)], config=metadata
        # print("response:: ", response)
        # return response
        # return "test response"
        return component_pipeline_query_hf(user_message, 20)
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))
        
################ Function call for progress feedback ################
    
def callLLM_progress_checker(cellStates, solutionCellStates, completed, levelMeaning, past_messages=[]):
    
    try:
        cellStates, solutionCellStates, width, height = reformat_cellStates(cellStates, solutionCellStates)
        differences = compare_grids(cellStates, solutionCellStates)
        wrong_selections = differences["wrong_selection"]
        missing_selections = differences["missing_selection"]
        
        if completed and (wrong_selections == [] and missing_selections == []):
            system_message = f"""Tell the user that the level is completed and congratulate them."""
            user_message = ""
            llm.model_kwargs["max_tokens"] = 10
            llm.model_kwargs["system_message"] = system_message
            llm.model_kwargs["history"] = past_messages
            
            response = llm.invoke(input=user_message) # [HumanMessage(content=user_message)], config=metadata
            print("response:: ", response)
            if 'error' in response:
                return "Server error:: " + response["error"]
            return response

        else:
            #### Using Azure LLM to generate a response from scratch
            # wrong_selections_sentences, missing_selections_sentences = generate_mistake_markers(differences)
            _, solutionCellStates = print_format_cellStates(cellStates, solutionCellStates)
            # system_message = system_prompt(cellStates, solutionCellStates, levelMeaning, height, width, wrong_selections_sentences, missing_selections_sentences)
            

            # print("system_message:: ", system_message)
            user_message = "Level Check Pipeline"
            llm.model_kwargs["max_tokens"] = 100
            
            #### Using sub component LLMs to generate a response
            start_time = time.time() 
            #           Choose a random mistake to talk about
            # system_message_random_pos = system_prompt_random(wrong_selections, missing_selections)
            # print("system_message_random_pos:: ", system_message_random_pos)
            # random_position_response = component_pipeline_query_hf(system_message_random_pos)
            # print("random_position LLM:: ", random_position_response)
            # print("cellStates:: ", cellStates)
            # print("wrong_selections:: ", wrong_selections)
            # print("missing_selections:: ", missing_selections)
            random_position = random_element(wrong_selections, missing_selections)
            # print("random_position:: ", random_position)
            
            #           Describe the position in simple natural language
            position_description = describe_point_position(random_position, width, height)
            print("Backend position description:: ", position_description)
            
            #           Formulate a phrase describing the position
            system_message_positioning = system_prompt_positioning(height, width, random_position, position_description)
            # print("system_message:: ", system_message_positioning)
            positioning_response_prev = (component_pipeline_query_hf(system_message_positioning, 20))
            positioning_response = filter_crop_llm_response(positioning_response_prev)
            print("positioning LLM:: ", positioning_response)
            
            #           Use the position to observe the surroundings
            system_message_observation = system_prompt_observe_around(height, width, random_position, positioning_response, solutionCellStates)
            # print("system_message_observation:: ", system_message_observation)
            observation_response_prev = (component_pipeline_query_hf(system_message_observation, 50))
            observation_response = filter_crop_llm_response(observation_response_prev)
            print("observation LLM:: "+ observation_response + '\n||\n' + observation_response_prev)
            
            #           Use the observation and position description to give feedback
            system_message_hint = system_prompt_hint(positioning_response, observation_response)
            hint_response = filter_crop_llm_response(component_pipeline_query_hf(system_message_hint, 100))
            print("hint LLM:: ", hint_response)
            end_time = time.time()
            latency = end_time - start_time
            print(f"Overall LLM pipeline Latency: {latency} seconds")
            
            return hint_response
            # system_message = system_message_hint  

        # # return "test response"
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        print(error.info())
        print(error.read().decode("utf8", 'ignore'))
        
def filter_crop_llm_response(response):
    # only accept the sentence between the first ':' and '\n' 
    response = response.split("\n")[0]
    if ("'" in response):
        if (response[-1] == "'"):
            response = response[:-1]
    return response