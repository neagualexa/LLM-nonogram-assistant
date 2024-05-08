import urllib.request
import json
import time
import re
from typing import Dict
import azure.LLM_calls.azurecredentials as azurecredentials
from langchain_community.llms.azureml_endpoint import (
    AzureMLOnlineEndpoint,
    ContentFormatterBase
)
from system_prompt import (
    system_prompt, 
    system_prompt_positioning, system_prompt_positioning_llama, 
    system_prompt_observe_around, system_prompt_observe_around_llama,
    system_prompt_hint, system_prompt_hint_llama,
    system_prompt_nonograms,

    system_prompt_general_hint,
    system_prompt_directional_hint,
    system_prompt_directional_hint_2,
    system_prompt_conclusive_hint,
    system_prompt_meaning_hint
)
from grid_functions import (
    string_to_lists_grids, 
    compare_grids, 
    generate_mistake_markers, 
    print_format_cellStates, 
    random_element, 
    describe_point_position, 
    count_consecutive_cells, 
    decide_overall_area
)
from hf_inference import component_pipeline_query_hf
from data_collection import csv_handler_progress
'''
HELP: https://python.langchain.com/docs/integrations/chat/azureml_chat_endpoint
https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-models-llama?view=azureml-api-2
Only for chat models
'''

API_URL = azurecredentials.api_url_8b_3
API_KEY = azurecredentials.key_8b_3
hint_model          = "Azure Llama 3 8b Instruct" #"Azure Llama 2 70b chat"
observation_model   = "Azure Llama 3 8b Instruct" #"HF Mixtral-8x7B-Instruct-v0.1"
position_model      = "Azure Llama 3 8b Instruct" #"HF Mixtral-8x7B-Instruct-v0.1"

system_message = "You are NonoAI, a helpful assistant replying the user's questions regarding Nonogram/Griddler puzzles. Reply in short sentences."

class LlamaCustomContentFormatter(ContentFormatterBase):
    """Custom Content formatter for LLama extended from langchain's ContentFormatterBase"""

    def format_request_payload(self, prompt: str, model_kwargs: Dict) -> bytes:
        """Formats the request according to the chosen api"""
        prompt = ContentFormatterBase.escape_special_characters(prompt)
        # print("prompt:: ", prompt)
        # print("history:: ", model_kwargs.get("history"))
        request_payload = json.dumps(
            {
                "messages": [
                    {"role": "system", "content": model_kwargs.get("system_message")},      # langchain does the system message magic
                    *model_kwargs.get("history"),                                           # langchain does the memory magic
                    {"role": "user", "content": prompt}                                     # langchain adds the history into the prompt with System, AI, Human labels
                ],
                "temperature": model_kwargs.get("temperature"),                             # can add default value here
                "max_tokens": model_kwargs.get("max_tokens"),
            }
        )
        # print("request_payload:: ", request_payload)
        return str.encode(request_payload)

    def format_response_payload(self, output: bytes) -> str:
        """Formats response depending on the chosen api"""
        # print("output:: ", output)
        return json.loads(output)["choices"][0]["message"]["content"]
    
# NOTES on LLM Memory Management in the Content Formatter:
# conversation memory can be done through adding multiple messages (make sure JSON is correct, so comma at end)  -> memory preserved as we fetch it from DB
# OR through adding the conversation into the prompt (as langchain does it) -> memory lost at every app restart

content_formatter = LlamaCustomContentFormatter()

# Langchain's Azure LLM endpoint for chat
llm = AzureMLOnlineEndpoint(
    endpoint_url=API_URL,
    endpoint_api_type="serverless",
    endpoint_api_key=API_KEY,
    content_formatter=content_formatter,
    model_kwargs={"temperature": 0.8, "max_tokens": 50, "history": [], "system_message": ""},
)

################
################ Function call for chat message with Azure ################
################

def callAzureLLM(user_message, system_message=system_message, max_tokens=100, past_messages=[]):
    
    try:
        start_time = time.time() 
        llm.model_kwargs["history"] = past_messages
        llm.model_kwargs["system_message"] = system_message
        llm.model_kwargs["max_tokens"] = max_tokens
        response = llm.invoke(input=user_message, stop=["<|eot_id|>"]) # [HumanMessage(content=user_message)], config=metadata
        print("response:: ", response)
        
        end_time = time.time()
        overall_latency = end_time - start_time
        print(f"Azure LLM Latency: {overall_latency} seconds")
        return response, overall_latency
        # return "test response"
    
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))
        return "Error in callAzureLLM:: " + error.read().decode("utf8", 'ignore')

################       
################ Function call for progress feedback : """General rules hint"""  HINT LEVEL : 0 ################
################

def callLLM_general_hint(hint_id, past_messages=[]):
    """
    Function to call the Azure LLM for a general hint.
    The general hint is a hint that is not based on the user's progress, but rather a general hint that can be given at any time based on the rules of the puzzle.
    
    As the generated hint should not be repeated, the past_messages are used to keep track of the hints that have been given.
    """
    # print("callLLM_general_hint:: past_messages:: ", past_messages)
    
    try:
        system_message_general_hint = system_prompt_general_hint()
        user_message = "I am a beginner and need some help. Give me a different hint than before."
        
        response, latency = callAzureLLM(user_message, system_message=system_message_general_hint, max_tokens=50, past_messages=past_messages)
        print("callLLM_general_hint:: response:: ", response)
        
        if "Hint:" in response: response = response.split("Hint:")[1]       # told in system prompt to start with "Hint:"
        response = response.split('\n')[0].strip()                          # remove ending whitespace
        response = remove_after_last_punctuation(response)                  # remove unfinished sentences
        
        try:
            ############ Save CSV entry
            new_entry_attributes = {'Hint_Response': response, 'Overall_Latency': latency, 'Hint_Latency': latency, 'Hint_Model': hint_model}
            csv_handler_progress.update_entry(hint_id, new_entry_attributes)     
        except Exception as e:
            print("Error in saving CSV entry:: ", e)   
        
        return response
    except Exception as e:
        print("callLLM_general_hint:: The request failed with status code: " + str(e))
        return "Error in callLLM_general_hint:: " + str(e)

################
################ Function call for progress feedback : """Directional hint"""    HINT LEVEL : 1 ################
################

def callLLM_directional_hint(cellStates, solutionCellStates, completed, hint_id, next_recommended_steps, no_next_steps, no_possible_combinations, line_index, line_index_clue, last_location, past_messages=[]):
    """
    Function to call the Azure LLM for progress feedback with a directional hint.
    The directional aspect depends on the next few best steps it is predicted for the user to take in order to solve the puzzle.
    Returns directional instructions to the user based on the next recommended steps (e.g. position in the grid, row number).
    """
    try:
        print("Entering callLLM_directional_hint:: next_recommended_steps:: ", next_recommended_steps, " last_location:: ", last_location)
        if completed:
            return "The puzzle is already completed. No further steps needed."
        else:
            height = len(cellStates)
            width = len(cellStates[0])
            
            # # 1. Get a natural language description of the locayions of the next recommended steps
            # locations_next_steps = [describe_point_position((step[0], step[1]), width, height) for step in next_recommended_steps]
            # print("locations_next_steps:: ", locations_next_steps)
            # # 2. Use the locations for each step and decide on overall area to focus on
            # overall_area = decide_overall_area(locations_next_steps)
            # print("overall_area:: ", overall_area)
            # 3. Get line index for overall steps (either row or column)
            print("line_index:: ", line_index, " has no_possible_combinations:: ", no_possible_combinations, " with no_next_steps (definite cells):: ", no_next_steps)
            # 4. Get the respective clues for the line index
            print("line_index_clue:: ", line_index_clue)
            # 3. Generate a hint based on the area to focus on 
            system_message_conclusive_hint = system_prompt_directional_hint_2(height, width, line_index, no_possible_combinations, no_next_steps, line_index_clue)
            user_message = "Give me a hint on what to do next."
            # system_message_conclusive_hint = system_prompt_directional_hint(next_recommended_steps, height, width, overall_area, last_location)
            # user_message = "Guide me to the area or rows or columns that I need to focus on next to complete the puzzle. Forget about the previous location and overall area from previous hints."
            
            # return "test"
            response, latency = callAzureLLM(user_message, system_message=system_message_conclusive_hint, max_tokens=50, past_messages=past_messages)
            print("callLLM_directional_hint:: response:: ", response)
            
            if "Hint:" in response: response = response.split("Hint:")[1]       # told in system prompt to start with "Hint:"
            response = response.split('\n')[0].strip()                          # remove ending whitespace
            response = remove_after_last_punctuation(response)                  # remove unfinished sentences
            
            try:
                ############ Save CSV entry
                new_entry_attributes = {'Position': next_recommended_steps, 'Hint_Response': response, 'Overall_Latency': latency, 'Hint_Latency': latency, 'Hint_Model': hint_model, 'Position_Description': overall_area, 'Positioning_Response': last_location}
                csv_handler_progress.update_entry(hint_id, new_entry_attributes)     
            except Exception as e:
                print("Error in saving CSV entry:: ", e) 
            
            return response
        
    except Exception as e:
        print("callLLM_directional_hint:: The request failed with status code: " + str(e))
        return "Error in callLLM_directional_hint:: " + str(e)

################   
################ Function call for progress feedback : """Conclusive hint"""    HINT LEVEL : 2 ################
################

def callLLM_conclusive_hint(completed, next_recommended_steps, hint_id, past_messages=[]):
    """
    Function to call the Azure LLM for a conclusive hint.
    The conclusive hint is a direct answer to the user's question, providing the next best step to take in order to solve the puzzle.
    Returns at least one cell to correct.
    """
    try:
        print("Entering callLLM_conclusive_hint:: next_recommended_steps:: ", next_recommended_steps)
        if completed:
            return "The puzzle is already completed. No further steps needed."
        else:
            system_message_conclusive_hint = system_prompt_conclusive_hint(next_recommended_steps)
            user_message = "What is the next step to solve the puzzle?"
            
            response, latency = callAzureLLM(user_message, system_message=system_message_conclusive_hint, max_tokens=50, past_messages=[])
            print("callLLM_conclusive_hint:: response:: ", response)
            
            if "Hint:" in response: response = response.split("Hint:")[1]       # told in system prompt to start with "Hint:"
            response = response.split('\n')[0].strip()                          # remove ending whitespace
            response = remove_after_last_punctuation(response)                  # remove unfinished sentences
            
            try:
                ############ Save CSV entry
                new_entry_attributes = {'Position': next_recommended_steps, 'Hint_Response': response, 'Overall_Latency': latency, 'Hint_Latency': latency, 'Hint_Model': hint_model}
                csv_handler_progress.update_entry(hint_id, new_entry_attributes)     
            except Exception as e:
                print("Error in saving CSV entry:: ", e) 
            
            return response
        
    except Exception as e:
        print("callLLM_conclusive_hint:: The request failed with status code: " + str(e))
        return "Error in callLLM_conclusive_hint:: " + str(e)

################
################ Function call for progress feedback : """Meaning hint"""    HINT LEVEL : 7 ################
################

def callLLM_meaning_hint(completed, meaning_level, hint_id, past_messages=[]):
    """
    Function to call the Azure LLM for a meaning hint.
    The meaning hint is a hint that is given when the user has completed the puzzle and is looking for a riddle or meaning behind the puzzle.
    Returns a riddle or a meaning behind the puzzle.
    """
    try:
        if completed:
            system_message_meaning_hint = system_prompt_meaning_hint(meaning_level)
            user_message = system_message_meaning_hint
            
            response, latency = callAzureLLM(user_message, system_message="", max_tokens=50, past_messages=[])
            print("callLLM_meaning_hint:: response:: ", response)
            
            if "Hint:" in response: response = response.split("Hint:")[1]       # told in system prompt to start with "Hint:"
            response = response.split('\n')[0].strip()                          # remove ending whitespace
            response = remove_after_last_punctuation(response)                  # remove unfinished sentences
            
            try:
                ############ Save CSV entry
                new_entry_attributes = {'Hint_Response': response, 'Overall_Latency': latency, 'Hint_Latency': latency, 'Hint_Model': hint_model}
                csv_handler_progress.update_entry(hint_id, new_entry_attributes)     
            except Exception as e:
                print("Error in saving CSV entry:: ", e) 
            
            return "Puzzle meaning riddle: "  + response
        else:
            return "The puzzle is not completed yet. No meaning hint available."
        
    except Exception as e:
        print("callLLM_meaning_hint:: The request failed with status code: " + str(e))
        return "Error in callLLM_meaning_hint:: " + str(e)

################
################ Formating the response ################
################

def filter_crop_llm_response(response):
    """
    Function to filter and crop the response from the LLM.
    """
    # only accept the sentence until terminator
    terminator = ["#", "\n", "<|eot_id|>"]
    response = response.split("\n")[0]
    if any([term in response for term in terminator]):
        for term in terminator:
            if term in response:
                response = response.split(term)[0]
                break
    if (response[-1] == "'"):
        response = response[:-1]
    return response


def remove_after_last_punctuation(input_string):
    """
    Function removes everything after the last punctuation mark in the input string. Hence, removing any unfinished sentences.
    """
    # Find the last punctuation mark
    match = re.search(r'[!?.]', input_string[::-1])  # Reverse the string to find the last punctuation mark
    if match:
        last_punctuation_index = len(input_string) - match.start() - 1
        return input_string[:last_punctuation_index + 1]
    else:
        return input_string  # No punctuation found, return the original string
    

################
################ Function call for progress feedback :  """Directional hint"""  OLD VERSION ################
################ Available for reference for both Azure and HF Inference methods            ################
################
   
def callLLM_progress_checker(cellStates, solutionCellStates, completed, levelMeaning, hint_id, next_recommended_steps, past_messages=[]):
    """
    Function to call the Azure LLM for progress feedback with a directional hint.
    The directional aspect depends on the next few best steps it is predicted for the user to take in order to solve the puzzle.
    """
    
    try:
        # cellStates, solutionCellStates, width, height = string_to_lists_grids(cellStates, solutionCellStates) # already in list format
        width = len(cellStates[0])
        height = len(cellStates)
        differences = compare_grids(cellStates, solutionCellStates)
        wrong_selections = differences["wrong_selection"]
        missing_selections = differences["missing_selection"]
        
        if completed and (wrong_selections == [] and missing_selections == []):
            # TODO: give a hint on the puzzle meaning; only congratulate on first request when completed
            system_message_congrats = f"""Congratulate that the level is completed."""
            user_message = "How did I do?"
            
            response, _ = callAzureLLM(user_message, system_message=system_message_congrats, max_tokens=10, past_messages=[])
            print("response:: ", response)
            
            return response

        else:
            _, solutionCellStates = print_format_cellStates(cellStates, solutionCellStates)
            
            #### Using sub component LLMs to generate a response
            start_time = time.time() 
            #           Choose a random mistake to talk about
            # system_message_random_pos = system_prompt_random(wrong_selections, missing_selections)
            # print("system_message_random_pos:: ", system_message_random_pos)
            # random_position_response, _ = component_pipeline_query_hf(system_message_random_pos)
            # print("random_position LLM:: ", random_position_response)
            # print("cellStates:: ", cellStates)
            # print("wrong_selections:: ", wrong_selections)
            # print("missing_selections:: ", missing_selections)
            random_position = random_element(wrong_selections, missing_selections)
            print("random_position:: ", random_position)
            
            #           Describe the position in simple natural language
            position_description = describe_point_position(random_position, width, height)
            print("Backend position description:: ", position_description)
            
            #     1      Formulate a phrase describing the position
            # system_message_positioning = system_prompt_positioning(height, width, random_position, position_description)
            # # print("system_message:: ", system_message_positioning)
            # positioning_response_prev, positioning_latency = (component_pipeline_query_hf(system_message_positioning, 20))
            # positioning_response = filter_crop_llm_response(positioning_response_prev)
            # print("positioning LLM:: ", positioning_response)
            # # check if error from API
            # if "HF error" in positioning_response:
            #     return "API server ERROR"
            
            #     1      Formulate a phrase describing the position using Azure LLM llama 3 instruct
            user_message = "Tell me where the location is in the grid."
            # user_message = "Tell me where the location is in the grid. Start with \"Rephrased: '\"."
            system_message_positioning = system_prompt_positioning_llama(height, width, random_position, position_description)
            positioning_response_prev, positioning_latency = callAzureLLM(user_message, system_message=system_message_positioning, max_tokens=20, past_messages=[])
            positioning_response = filter_crop_llm_response(positioning_response_prev)
            # positioning_response = positioning_response.split("Rephrased:")[1]
            print("positioning LLM:: ", positioning_response)
            
            #    2       Use the position to observe the surroundings using HuggingFace
            # system_message_observation = system_prompt_observe_around(height, width, random_position, positioning_response, solutionCellStates)
            # # print("system_message_observation:: ", system_message_observation)
            # observation_response_prev, observation_latency = (component_pipeline_query_hf(system_message_observation, 100))
            # observation_response = filter_crop_llm_response(observation_response_prev)
            # print("observation LLM:: "+ observation_response)
            # # check if error from API
            # if "HF error" in observation_response:
            #     return "API server ERROR"
            
            #     2     Use the position to observe the surroundings using Azure LLM
            user_message = "Tell me about the cells in the vicinity."
            # user_message = "Tell me about the cells in the vicinity. Start with \"Observation: '\"."
            system_message_observation = system_prompt_observe_around_llama(height, width, random_position, positioning_response, solutionCellStates)
            # print("system_message_observation:: ", system_message_observation)
            observation_response_prev, observation_latency = callAzureLLM(user_message, system_message=system_message_observation, max_tokens=100, past_messages=[])
            observation_response = filter_crop_llm_response(observation_response_prev)
            # observation_response = observation_response.split("Observation:")[1]
            print("observation LLM:: "+ observation_response)
            
            #     3      Use the observation and position description to give feedback using HuggingFace
            # system_message_hint = system_prompt_hint(positioning_response, observation_response)
            # print("system_message_hint:: ", system_message_hint)
            # hint_response = filter_crop_llm_response(component_pipeline_query_hf(system_message_hint, 70))
            # print("HF - hint LLM:: ", hint_response)
            
            #     3      Use the observation and position description to give feedback using Azure LLM
            user_message = "Give me a hint in 1-2 sentences. What can I do next?"
            # user_message = "Give me a hint in 1-2 sentences based on the observation. Make sure to say where I made a mistake. Start with 'Hint:'."
            system_message_hint = system_prompt_hint_llama(positioning_response, observation_response, next_steps=next_recommended_steps, solutionCellStates=solutionCellStates)
            hint_response, hint_latency = callAzureLLM(user_message, system_message=system_message_hint, max_tokens=50, past_messages=[])
            # print("Llama2 - hint LLM:: ", hint_response)
            # Reshaping the response
            # hint_response = "".join(hint_response.split("Hint:")[1])    # only take the hint part
            hint_response = "".join(hint_response.split('\n'))          # remove the newlines
            # hint_response = ".".join(re.split(r'[!?.]', hint_response)[:-1])+"."
            hint_response = remove_after_last_punctuation(filter_crop_llm_response(hint_response))
            print("Llama2 - hint LLM:: ", hint_response)
            
            end_time = time.time()
            overall_latency = end_time - start_time
            print(f"Overall LLM pipeline Latency: {overall_latency} seconds")
            
            try:
                ############ Save CSV entry
                new_entry_attributes = {'Position': random_position, 'Hint_Response': hint_response, 'Observation_Response': observation_response, 'Positioning_Response': positioning_response, 'Position_Description': position_description, 'Overall_Latency': overall_latency, 'Hint_Latency': hint_latency, 'Observation_Latency': observation_latency, 'Position_Latency': positioning_latency, 'Hint_Model': hint_model, 'Observation_Model': observation_model, 'Position_Model': position_model, 'Mistakes_per_Hint_Wrong': len(wrong_selections), 'Mistakes_per_Hint_Missing': len(missing_selections)}
                csv_handler_progress.update_entry(hint_id, new_entry_attributes)     
            except Exception as e:
                print("Error in saving CSV entry:: ", e)   
            
            return hint_response
            # system_message = system_message_hint  

        # return "test response"
    except Exception as e:
        print("callLLM_progress_checker:: The request failed with status code: " + str(e))
        return "Error in callLLM_progress_checker:: " + str(e)