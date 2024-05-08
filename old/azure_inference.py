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
from grid_functions import string_to_lists_grids, compare_grids, generate_mistake_markers, print_format_cellStates, random_element, describe_point_position, count_consecutive_cells
from hf_inference import component_pipeline_query_hf
'''
HELP: https://python.langchain.com/docs/integrations/llms/azure_ml/
https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-models-llama?view=azureml-api-2 
Only for NON-chat models
'''

API_URL = azurecredentials.api_url_13
API_KEY = azurecredentials.key_13

system_message = "You are NonoAI, a helpful assistant replying the user's questions. Reply in short sentences."
# system_message = """You are the Nonogram Solver Assistant. You can help the user tackle nonogram and griddler puzzles with ease. Whether the user is a beginner or an experienced puzzle enthusiast, you are ready to assist them in solving these challenging puzzles. 
#             The user can describe the puzzle or ask for specific tips, and you will guide them through the solving process.
#             You can also engage in some casual talk, like answering greetings and simple questions like "How/Who are you?". 
#             At the beginning of a conversation in your first message, introduce yourself. 
#             Always start with ASSISTANT: when responding to the question.
#             DO NOT COMPLETE THE SENTENCE!
#             ONLY answer the user's questions regarding Nonograms. If you do not know how to answer, reply by saying you do not know. Do not reply to any irrelevant questions."""

class LlamaCustomContentFormatter(ContentFormatterBase):
    """Custom Content formatter for LLaMa 2"""
    
    content_type = "application/json"
    accepts = "application/json"

    def format_request_payload(self, prompt: str, model_kwargs: Dict) -> bytes:
        input_str = json.dumps(
            {
                "prompt": [prompt],
                "temperature": model_kwargs.get("temperature"),             # can add default value here
                "max_tokens": model_kwargs.get("max_tokens"),
            }
        )
        print("input_str:: ", input_str)
        return str.encode(input_str)

    def format_response_payload(self, output: bytes) -> str:
        """Formats response"""
        print("output:: ", output)
        response_json = json.loads(output)
        return response_json["choices"][0]["text"]

content_formatter = LlamaCustomContentFormatter()

llm = AzureMLOnlineEndpoint(
    endpoint_url=API_URL,
    endpoint_api_type="serverless",
    endpoint_api_key=API_KEY,
    content_formatter=content_formatter,
    model_kwargs={"temperature": 0.8, "max_tokens": 50},
)
        
################ Function call for progress feedback ################
    
def callLLM_progress_checker(cellStates, solutionCellStates, completed, levelMeaning, past_messages=[]):
    
    try:
        # cellStates, solutionCellStates, width, height = string_to_lists_grids(cellStates, solutionCellStates)
        width = len(cellStates[0])
        height = len(cellStates)
        differences = compare_grids(cellStates, solutionCellStates)
        wrong_selections = differences["wrong_selection"]
        missing_selections = differences["missing_selection"]
        
        if completed and (wrong_selections == [] and missing_selections == []):
            system_message = f"""Tell the user that the level is completed and congratulate them."""
            user_message = ""
            llm.model_kwargs["max_tokens"] = 10
            # llm.model_kwargs["system_message"] = system_message
            # llm.model_kwargs["history"] = past_messages
            
            response = llm.invoke(system_message)
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
            print("random_position:: ", random_position)
            
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
            observation_response_prev = (component_pipeline_query_hf(system_message_observation, 100))
            observation_response = filter_crop_llm_response(observation_response_prev)
            print("observation LLM:: "+ observation_response + '\n||\n' + observation_response_prev)
            
            #           Use the observation and position description to give feedback
            system_message_hint = system_prompt_hint(positioning_response, observation_response)
            print("system_message_hint:: ", system_message_hint)
            hint_response = filter_crop_llm_response(component_pipeline_query_hf(system_message_hint, 70))
            print("HF - hint LLM:: ", hint_response)
            
            # user_message = "Level Check Pipeline"
            llm.model_kwargs["max_tokens"] = 100
            # llm.model_kwargs["system_message"] = system_message_hint
            # llm.model_kwargs["history"] = past_messages
            
            hint_response = llm.invoke(input=system_message_hint)
            if 'error' in hint_response:
                return "Server error:: " + hint_response["error"]
            
            print("Llama2 - hint LLM:: ", hint_response)
            end_time = time.time()
            latency = end_time - start_time
            print(f"Overall LLM pipeline Latency: {latency} seconds")
            
            return hint_response
            # system_message = system_message_hint  

        # return "test response"
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