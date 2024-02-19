from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import requests
# from huggingface_inference import query as callLLM
# from llm_local import callLLM
from azure_inference import callLLM

app = Flask(__name__)

# Chatbot name
chatbot_name = "Your Chatbot"

# Variable to store messages
# messages_cache = []

# SQLite Database Initialization
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT NOT NULL,
        bot_message TEXT NOT NULL,
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
    return render_template('index.html', messages=messages, chatbot_name=chatbot_name)

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form.get('user_message')
    print('user_message:: '+user_message)
    
    ############################################## call LLM for response
    response = callLLM(user_message)
    #####
    # url = 'http://127.0.0.1:5001/predict'
    # data = {'input_data': user_message}
    # response = requests.post(url, json=data)
    # print("response:: ", response)
    # response = response.json()['result']
    ############################################## 

    # Add user message to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (user_message, bot_message) VALUES (?, ?)',
                (user_message, response))
    conn.commit()
    
    # # Fetch the new message
    # cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 1')
    # new_message = cursor.fetchone()
    # conn.close()
    
    # Update the messages cache
    # messages_cache.insert(0, new_message)

    return redirect('/')

@app.route('/clear_history')
def clear_history():
    # Clear all messages from the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages')
    conn.commit()
    conn.close()
    # # Clear the messages cache
    # global messages_cache
    # messages_cache = []

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
