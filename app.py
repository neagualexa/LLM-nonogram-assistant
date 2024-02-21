from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import requests
# from huggingface_inference import query as callLLM
# from llm_local import callLLM
# from azure_inference import callLLM
from azure_inference_chat import callLLM

app = Flask(__name__)

# Chatbot name
chatbot_name = "Your Chatbot"

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
