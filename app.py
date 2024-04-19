from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import requests
import json
# from old.huggingface_inference import query as callLLM  # hugging face llms
# from old.llm_local import callLLM                       # local gguf file llm
# from old.azure_inference_http import callLLM            # azure llm but pure http requests
from azure_inference_chat import callAzureLLM, callLLM_progress_checker                # azure llm with langchain and embedded message history (preferred as memory preserved in DB)
# from old.azure_inference import callLLM_progress_checker                            # azure llm non chat
# from old.llm_chain_memory import callLLM                # azure llm with langchain and llm chain memory (memory lost at every app restart)
from puzzle_checker_inference import meaning_checker_hf   # HF llm checking validity of user meaning
from data_collection import csv_handler_progress, csv_handler_meaning, csv_handler_game

app = Flask(__name__)

# Chatbot name
chatbot_name = "NonoAI"

# Variable to store messages
messages_cache = []

# SQLite Database Initialization
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT NOT NULL,
        ai_message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC')
    messages = cursor.fetchall()
    conn.close()
    # format the messages into json for user and ai and timestamp
    messages = [{'user_message': message[1], 'ai_message': message[2], "timestamp": message[3]} for message in messages]
    global messages_cache
    messages_cache = format_history(messages)
    return render_template('index.html', messages=messages, chatbot_name=chatbot_name)

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form.get('user_message')
    print('user_message:: ', user_message)
    
    ############################################## call LLM for response
    response, _ = callAzureLLM(user_message, messages_cache)
    #####
    # url = 'http://127.0.0.1:5001/predict'
    # data = {'input_data': user_message}
    # response = requests.post(url, json=data)
    # print("response:: ", response)
    # response = response.json()['result']
    ############################################## 

    if response:
        # Add user message to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (user_message, ai_message) VALUES (?, ?)',
                    (user_message, response))
        conn.commit()
        
        # Fetch the new message
        cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 1')
        new_message = cursor.fetchone()
        conn.close()
        new_message = {'user_message': new_message[1], 'ai_message': new_message[2], "timestamp": new_message[3]}
        
        # Update the messages cache
        messages_cache.insert(0, (m for m in format_message(new_message)))

    redirect('/')
    
    return response

@app.route('/check_puzzle_meaning', methods=['POST'])
def check_puzzle_meaning():
    # Get puzzleMeaning from the form
    puzzle_meaning = request.form.get('puzzleMeaning')
    # Load puzzle meaning from string to json
    # print("puzzle_meaning:: ", puzzle_meaning)
    puzzle_meaning = json.loads(puzzle_meaning)
    user_guess = puzzle_meaning['user_guess']
    solution = puzzle_meaning['solution']
    username = puzzle_meaning['username']
    level = puzzle_meaning['level']
    
    response, meaning_latency = meaning_checker_hf(user_guess, solution)
    
    # Save the data to the CSV database
    count_entries = len(csv_handler_meaning.read_entries())
    new_entry = {'id': count_entries, 'User': username, 'Level': level, 'Meaning': solution, 'Guess': user_guess, 'Approved': response, 'Model': 'HF LaMini-Flan-T5-783M', 'Latency': meaning_latency, 'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    csv_handler_meaning.add_entry(new_entry)
    
    return response

@app.route('/check_puzzle_progress', methods=['POST'])
def check_puzzle_progress():
    # Get puzzleMeaning from the form
    puzzle_progress = request.form.get('puzzleProgress')
    # Load puzzle meaning from string to json
    # print("puzzle_progress:: ", puzzle_progress)
    puzzle_progress = json.loads(puzzle_progress)
    cellStates = puzzle_progress['cellStates']
    solutionCellStates = puzzle_progress['solutionCellStates']
    completed = True if puzzle_progress['completed'].lower() == "true" else False # convert to boolean
    levelMeaning = puzzle_progress['levelMeaning']
    username = puzzle_progress['username']
    level = puzzle_progress['level']
    hint_id = puzzle_progress['hint_id']
    
    ##### Save the data to the CSV Progress database
    if not completed:
        # count_entries = len(csv_handler_progress.read_entries())
        new_entry = {'id': hint_id, 'User': username, 'Level': level, 'Position': 'test', 'Hint_Response': 'test', 'Observation_Response': 'test', 'Positioning_Response': 'test', 'Position_Description': 'test', 'Overall_Latency': 'test', 'Hint_Latency': 'test', 'Observation_Latency': 'test', 'Position_Latency': 'test', 'Hint_Model': 'test', 'Observation_Model': 'test', 'Position_Model': 'test', 'Mistakes_per_Hint_Wrong': 0, 'Mistakes_per_Hint_Missing': 0, 'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        csv_handler_progress.add_entry(new_entry)
    ############################################## call LLM for response
    response_llm = callLLM_progress_checker(cellStates, solutionCellStates, completed, levelMeaning, hint_id, messages_cache)
    #####
    try:
        url = 'http://localhost:5005/verbal_hint'
        data = {'responseText': response_llm, 'counter': 0}
        response = requests.post(url, data=data)
        print("response from verbal_hint:: ", response)
    except Exception as e:
        print("error in /check_puzzle_progress connecting to /verbal_hint:: ", e)
    ############################################## 

    if response_llm:
        # Add user message to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (user_message, ai_message) VALUES (?, ?)',
                    ("Progress feedback:", response_llm))
        conn.commit()
        
        # Fetch the new message
        cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 1')
        new_message = cursor.fetchone()
        conn.close()
        new_message = {'user_message': new_message[1], 'ai_message': new_message[2], "timestamp": new_message[3]}
        
        # Update the messages cache
        messages_cache.insert(0, (m for m in format_message(new_message)))

    redirect('/')
    # refresh page
    # return redirect('/')
    return response_llm

@app.route('/verbalise_hint', methods=['POST'])
def verbalise_hint():
    hint = json.loads(request.form.get('hint'))
    try:
        url = 'http://localhost:5005/verbal_hint'
        data = {'responseText': hint['hint'], 'counter': 0}
        response = requests.post(url, data=data)
        # print("response from verbal_hint:: ", response)
        return "Hint successfully verbalised!"
    except Exception as e:
        print("error in /verbalise_hint connecting to /verbal_hint:: ", e)
        return "Error in /verbalise_hint connecting to /verbal_hint: " + e
        
@app.route('/clear_history')
def clear_history():
    # Clear all messages from the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages')
    conn.commit()
    conn.close()
    # Clear the messages cache
    global messages_cache
    messages_cache = []

    return redirect('/')

@app.route('/end_game', methods=['POST'])
def save_game():
    userGameData = request.form.get('EndGameData').lower() # lower() to avoid case sensitivity between boolean in python and c#
    # print("userGameData:: ", userGameData)
    userGameData = json.loads(userGameData)
    levels_data = userGameData['levels_data']
    for i in range(len(levels_data)):
        level_data = levels_data[str(i)]
        new_entry = {'id': len(csv_handler_game.read_entries()), 'User': userGameData['username'], 'Level': level_data['level'], 'Completed': level_data['level_completed'], 'onTime': level_data['on_time'], 'Duration': level_data['time'], 'Meaning_Completed': level_data['meaning_completed'], 'Nb_Hints_Used': level_data['nb_hints_used'], 'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        print("new_entry:: ", new_entry)
        csv_handler_game.add_entry(new_entry)
        
    return "Game data saved successfully!"

def format_message(message):
    formatted_message = [
        {"role": "user", "content": message["user_message"]},
        {"role": "assistant", "content": message["ai_message"]},
    ]
    return formatted_message
def format_history(messages):
    formatted_messages = [m for message in messages for m in format_message(message)]
    return formatted_messages

if __name__ == '__main__':
    app.run(debug=True)
