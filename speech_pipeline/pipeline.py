import speech_to_text
import text_to_speech
import audio_functions
import time
import os
import requests

# Accepted file formats: wav, ogg, flac
# pipeline_file = "./samples/pipeline.wav"

# url = 'http://localhost:5000/process'

def speech_pipeline(file_path):
    print("Speech Pipeline...")

    wait_until_file_exists(file_path)
    
    # wav file expected
    transcription = speech_to_text.transcribe_audio(file_path)
    print("Transcription of original: ", transcription)
    
    print("Passing to LLM...") 
    llm_response = connect_to_llm(transcription) #[0]) #models
    print("LLM response:: ", llm_response)
    
    if llm_response == None:
        print("LLM response is None")
        return
    if "connect_to_llm Error:" in llm_response:
        print("ERROR:: LLM response error")
        return
    
    output_file_path = "."+file_path.split(".")[1] + "_response.wav"
    print("Output file: ", output_file_path, " from ", file_path)
    speech = text_to_speech.get_audio_from_text(llm_response, output_file_path)  ## TESTING - works on ubuntu not on langchain image
    
    audio_functions.convert_to_standard_wav(output_file_path) # google tts does not save as standard wav
    audio_functions.play_audio(output_file_path)
    
    # HTTP POST request to share the audio file to a server IP
    # print("Sharing transcript and audio to server...")
    # # share_transcript_audio(llm_response, url, output_file_path)            # sending llm TRANSCRIPT and AUDIO 
    # # share_transcript_audio(llm_response, pipeline_file, url)          # sending llm TRANSCRIPT and AUDIO
    # share_transcript_audio("test Pipeline file",url , pipeline_file)    # sending dummy TRANSCRIPT and dummy AUDIO

def verbalise_hint(hint_text, counter):
    print("Verbalising hint...")

    # text to speech
    output_file_path = "./speech_pipeline/verbal_hints/hint_" + str(counter) + ".wav"
    print("Output file: ", output_file_path)
    speech = text_to_speech.get_audio_from_text(hint_text, output_file_path)  ## TESTING - works on ubuntu not on langchain image
    
    audio_functions.convert_to_standard_wav(output_file_path) # google tts does not save as standard wav
    audio_functions.play_audio(output_file_path)
    
    # HTTP POST request to share the audio file to a server IP
    # print("Sharing hint audio to server...")
    # share_transcript_audio(hint_text, url, output_file_path)            # sending hint TRANSCRIPT and
        
def connect_to_llm(transcription):
    """ 
        Connect to LLM 
    """
        
    ai_url = 'http://localhost:5000/send_message'
    
    # add transcription into form data
    data = {'user_message': transcription}
    print("Transcription data: ", data)
    response = requests.post(ai_url, data=data)
    
    if response.status_code != 200:
        print('connect_to_llm Error: Failed to get response from LLM. Status code: ', response.status_code)
        return 'connect_to_llm Error: Failed to get response from LLM. Status code: ', response.status_code
    llm_response = response.text
    # print("LLM response: ", llm_response)
    return llm_response
    
    
def wait_until_file_exists(file_path):
    """
        Wait until the file exists in the directory
    """
    time_count = 0
    while not os.path.exists(file_path) :
        print("Waiting for file: ", file_path)
        time.sleep(1)
        if time_count == 5:
            print("File not found: ", file_path)
            return
        time_count+=1
    return "wait_until_file_exists: Error on opening file "+ file_path

def share_transcript_audio(transcript, url, file_path=""):
    """
        HTTP POST request to share the transcript to a server IP
    """
    
    print("share_transcript Transcript: ", transcript)
    print("share_output_audio File path: ", file_path)
    
    # if transcript == None: transcript = "..."
    json_transcript = {"transcript": transcript}
    print(json_transcript)
    
    if file_path == "":
        print("---- Sending transcript only")
        response = requests.post(url, json=json_transcript) # sending llm TRANSCRIPT to JS website
    else:
        print("---- Sending transcript and audio")
        files = {"audioFile": open(file_path, 'rb')}
        response = requests.post(url, data=json_transcript, files=files) # sending llm TRANSCRIPT and AUDIO to JS website
        
    if response.status_code == 200:
        print('share_transcript Transcript successfully posted.')
    else:
        print(f'share_transcript Failed to post transcript. Status code: {response.status_code}')

