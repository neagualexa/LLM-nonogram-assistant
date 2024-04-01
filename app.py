from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import requests
import json
# from huggingface_inference import query as callLLM    # hugging face llms
# from llm_local import callLLM                         # local gguf file llm
# from azure_inference import callLLM                   # azure llm but pure http requests
from azure_inference_chat import callLLM, callLLM_progress_checker                # azure llm with langchain and embedded message history (preferred as memory preserved in DB)
# from llm_chain_memory import callLLM                  # azure llm with langchain and llm chain memory (memory lost at every app restart)
from puzzle_checker_inference import meaning_checker_hf   # HF llm checking validity of user meaning

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
    print('user_message:: '+user_message)
    
    ############################################## call LLM for response
    response = callLLM(user_message, messages_cache)
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

    return redirect('/')

@app.route('/check_puzzle_meaning', methods=['POST'])
def check_puzzle_meaning():
    # Get puzzleMeaning from the form
    puzzle_meaning = request.form.get('puzzleMeaning')
    # Load puzzle meaning from string to json
    # print("puzzle_meaning:: ", puzzle_meaning)
    puzzle_meaning = json.loads(puzzle_meaning)
    user_guess = puzzle_meaning['user_guess']
    solution = puzzle_meaning['solution']
    
    response = meaning_checker_hf(user_guess, solution)
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
    completed = True if puzzle_progress['completed'].lower() == "true" else False
    levelMeaning = puzzle_progress['levelMeaning']
    
    # print("cellStates:: ", cellStates, "solutionCellStates:: ", solutionCellStates, "completed:: ", completed, "levelMeaning:: ", levelMeaning)
    ############################################## call LLM for response
    response = callLLM_progress_checker(cellStates, solutionCellStates, completed, levelMeaning, messages_cache)
    ############################################## 

    if response:
        # Add user message to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (user_message, ai_message) VALUES (?, ?)',
                    ("Progress feedback:", response))
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
    return response

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
