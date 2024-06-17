from flask import Flask, request
from flask_cors import CORS
from threading import Lock
from pipeline import speech_pipeline, verbalise_hint
import time
from datetime import datetime
import os
from data_collection import csv_handler_audio

app = Flask(__name__)
# add cors support
CORS(app)
# to block multiple requests on same route
lock = Lock()

UPLOAD_FOLDER = './conversation'

@app.route('/', methods=['POST'])
def index():
    return 'Speech Server is running', 200

@app.route('/verbal', methods=['POST'])
def synth():
    start_time = time.time()
    try:
        print("Received request to synthesize text")
        
        if 'audioFile' not in request.files:
            return 'No file part'

        audio_file = request.files['audioFile']
        if audio_file.filename == '':
            return 'No selected file'

        file_path = './speech_pipeline/conversation/'+ audio_file.filename 
        # fileName = request.form['fileName']     
        print(audio_file, file_path, file_path.split(".")[2])
        
        
        # Save the file to the './conversation' directory
        audio_file.save(file_path)
        print("File saved")

        # Process the file using your speech_pipeline function
        speech_pipeline(file_path)
        # delete the original file
        # os.remove(file_path)
        end_time = time.time()
        print("/verbal :: Time taken: ", end_time-start_time) 
        
        return 'File successfully received and processed! on file: ' + file_path
    
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        os.remove(file_path)
        return 'Error processing file', 500
    
@app.route('/verbal_hint', methods=['POST'])
def ai_hint():
    # do not let another request to be processed until the previous one is done
    with lock:
        start_time = time.time()
        try:
            print("Received request to generate audio for AI response text")
            
            # Get the text from the request
            pre_text = ""#"Hi! Here is a hint: "
            response_text = request.form['responseText']
            counter = request.form['counter']
            hint_level = request.form['hint_level']
            hint_id = request.form['hint_id']
            print(counter, pre_text + response_text)
            
            # text to speech
            file_path = './speech_pipeline/conversation/' + counter + '.mp3'
            audio_duration = verbalise_hint(pre_text + response_text, counter)
            end_time = time.time()
            # time lapse also contains the time taken to play the audio file     
            gen_time_taken = end_time-start_time-audio_duration   
            print("/verbal_hint :: Time taken: ", gen_time_taken, "; audio duration to play out loud: ", audio_duration)  

            # save the audio file data to the csv file
            try:
                id = csv_handler_audio.get_length() + 1
                csv_handler_audio.add_entry({'id': id, 'Hint_Id': hint_id, 'Hint_Level': hint_level,'Hint': response_text, 'Audio_Generation_Latency': gen_time_taken, 'Audio_Playback_Latency': audio_duration, 'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            except Exception as e:
                print(f"Error writing to csv: {str(e)}")
            
            return 'File successfully received and processed! on file: ' + file_path
        
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            os.remove(file_path)
            return 'Error processing file', 500
    
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
