from flask import Flask, request
from flask_cors import CORS
from pipeline import speech_pipeline, verbalise_hint
import time
import os

app = Flask(__name__)
# add cors support
CORS(app)

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
        print("Time taken: ", end_time-start_time)  #TODO: to be saved in a csv file alongside audio duration and response duration and level
        
        return 'File successfully received and processed! on file: ' + file_path
    
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        os.remove(file_path)
        return 'Error processing file', 500
    
@app.route('/verbal_hint', methods=['POST'])
def ai_hint():
    start_time = time.time()
    try:
        print("Received request to generate audio for AI response text")
        
        # Get the text from the request
        pre_text = "Hi! Here is a hint: "
        response_text = request.form['responseText']
        counter = request.form['counter']
        print(counter, pre_text + response_text)
        
        # text to speech
        file_path = './speech_pipeline/conversation/' + response_text + '.mp3'
        verbalise_hint(pre_text + response_text, counter)
        
        
        return 'File successfully received and processed! on file: ' + file_path
    
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        os.remove(file_path)
        return 'Error processing file', 500
    
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
