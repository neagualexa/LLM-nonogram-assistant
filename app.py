from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import requests
import json
import ast
# from old.huggingface_inference import query as callLLM  # hugging face llms
# from old.llm_local import callLLM                       # local gguf file llm
# from old.azure_inference_http import callLLM            # azure llm but pure http requests
from azure_inference_chat import (          
    callAzureLLM,                   # azure llm with langchain and embedded message history (preferred as memory preserved in DB)
    callLLM_progress_checker,
    callLLM_general_hint,
    callLLM_directional_hint,
    callLLM_conclusive_hint
)                
# from old.azure_inference import callLLM_progress_checker                            # azure llm non chat
# from old.llm_chain_memory import callLLM                # azure llm with langchain and llm chain memory (memory lost at every app restart)
from puzzle_checker_inference import meaning_checker_hf   # HF llm checking validity of user meaning
from data_collection import csv_handler_progress, csv_handler_meaning, csv_handler_game, csv_handler_interaction
from grid_difference_checker import count_consecutive_cells
from progress_tracking import (
    recommend_next_steps,
    calculate_progress, track_user_level_progress, define_hint_level,
    user_level_progress
)

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
    global messages_cache
    messages = fetch_messages_cached()
    messages_cache = format_history(messages)
    return render_template('index.html', messages=messages, chatbot_name=chatbot_name)

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form.get('user_message')
    print('user_message:: ', user_message)
    
    ############################################## call LLM for response
    system_prompt = "You are NonoAI, a helpful assistant replying the user's questions regarding Nonogram/Griddler puzzles. Reply in short sentences."
    response, _ = callAzureLLM(user_message, system_message=system_prompt, max_tokens=50, past_messages=messages_cache)
    #####
    # url = 'http://127.0.0.1:5001/predict'
    # data = {'input_data': user_message}
    # response = requests.post(url, json=data)
    # print("response:: ", response)
    # response = response.json()['result']
    ############################################## 

    if response:
        # Add conversation to the database
        insert_new_message_cache(user_message, response)

    redirect('/')
    
    return response

@app.route('/check_puzzle_meaning', methods=['POST'])
def check_puzzle_meaning():
    # Get puzzleMeaning from the form
    puzzle_meaning = request.form.get('puzzleMeaning')
    # Load puzzle meaning from string to json
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
    puzzle_progress = json.loads(puzzle_progress)
    cellStates = puzzle_progress['cellStates']
    solutionCellStates = puzzle_progress['solutionCellStates']
    cellStates = ast.literal_eval(cellStates)
    solutionCellStates = ast.literal_eval(solutionCellStates)
    completed = True if puzzle_progress['completed'].lower() == "true" else False # convert to boolean
    levelMeaning = puzzle_progress['levelMeaning']
    username = puzzle_progress['username']
    level = puzzle_progress['level']
    hint_id = puzzle_progress['hint_id']

    # calculate progress of user and update the hint level accordingly
    progress = calculate_progress(progressGrid=cellStates, solutionGrid=solutionCellStates)
    track_user_level_progress(username, level, progress)
    define_hint_level(username, level)
    # print("user_level_progress:: ", user_level_progress, progress)
    hint_level = user_level_progress[username]["hint_level"]
    # hint_level = 1 # for testing
    
    if hint_level > 0:
        ##### Fetch the last interactions
        if len(csv_handler_interaction.read_entries()) == 0:
            hint_level = 0
            next_recommended_steps = []
        else:
            last_interactions_entry = csv_handler_interaction.read_entries()[-1]
            lastPressedCell_1 = ast.literal_eval(last_interactions_entry['Cell_1']) if last_interactions_entry['Cell_1'] else None # lsit of 4 elements (Row, Column, Row Group Size, Column Group Size)
            lastPressedCell_2 = ast.literal_eval(last_interactions_entry['Cell_2']) if last_interactions_entry['Cell_2'] else None
            lastPressedCell_3 = ast.literal_eval(last_interactions_entry['Cell_3']) if last_interactions_entry['Cell_3'] else None
            
            # predict next best steps
            row_clues, column_clues = count_consecutive_cells(solutionCellStates)
            last_interactions = [lastPressedCell_1, lastPressedCell_2, lastPressedCell_3]
            next_recommended_steps, _ = recommend_next_steps(no_next_steps=3, progressGrid=cellStates, solutionGrid=solutionCellStates, last_interactions=last_interactions, row_clues=row_clues, column_clues=column_clues)
    
    ##### Save the data to the CSV Progress database
    if not completed:
        # count_entries = len(csv_handler_progress.read_entries())
        new_entry = {'id': hint_id, 'Hint_Level': hint_level, 'User': username, 'Level': level, 'Position': '', 'Hint_Response': '', 'Observation_Response': '', 'Positioning_Response': '', 'Position_Description': '', 'Overall_Latency': '', 'Hint_Latency': '', 'Observation_Latency': '', 'Position_Latency': '', 'Hint_Model': '', 'Observation_Model': '', 'Position_Model': '', 'Mistakes_per_Hint_Wrong': 0, 'Mistakes_per_Hint_Missing': 0, 'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        csv_handler_progress.add_entry(new_entry)
        
    ############################################## call LLM for response depending on the hint level
    messages_cache = format_history(fetch_last_5_messages_cached())
    response_llm = ""
    if hint_level == 0:
        """General rules hint"""
        response_llm = callLLM_general_hint(hint_id, messages_cache)
    elif hint_level == 1:
        """Directional hint"""
        response_llm = callLLM_directional_hint(cellStates, solutionCellStates, completed, levelMeaning, hint_id, next_recommended_steps, messages_cache)
    elif hint_level == 2:
        "Conclusive hint"
        response_llm = callLLM_conclusive_hint(completed, next_recommended_steps, hint_id, messages_cache)
    #####
    # try:
    #     url = 'http://localhost:5005/verbal_hint'
    #     data = {'responseText': response_llm, 'counter': 0}
    #     response = requests.post(url, data=data)
    #     print("response from verbal_hint:: ", response)
    # except Exception as e:
    #     print("error in /check_puzzle_progress connecting to /verbal_hint:: ", e)
    ############################################## 

    if response_llm != "":
        # Save conversation to the database
        message = f"Progress feedback HINT LEVEL {hint_level}"
        insert_new_message_cache(message, response_llm)
        
    # redirect('/')
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

@app.route('/record_interaction', methods=['POST'])
def record_interactions():
    interactions = request.form.get('GridInteractions')
    interactions = json.loads(interactions)
    username = interactions["username"]
    level = interactions["level"]
    lastPressedCell_1 = interactions["lastPressedCell_1"] # lsit of 4 elements (Row, Column, Row Group Size, Column Group Size)
    lastPressedCell_2 = interactions["lastPressedCell_2"]
    lastPressedCell_3 = interactions["lastPressedCell_3"]
    solutionGrid = interactions["solutionGrid"]
    solutionGrid = ast.literal_eval(solutionGrid)
    progressGrid = interactions["progressGrid"]
    progressGrid = ast.literal_eval(progressGrid)
    
    # each Cell_i is a list of  (Row, Column, Row Group Size, Column Group Size)
    ##### Save the data to the CSV Interaction database
    new_entry = {'id': len(csv_handler_interaction.read_entries()), 'User': username, 'Level': level, 'Cell_1': lastPressedCell_1, 'Cell_2': lastPressedCell_2, 'Cell_3': lastPressedCell_3, 'Grid': solutionGrid, 'Progress_Grid': progressGrid, 'Target_row': 'x', 'Target_col': 'y'}    
    csv_handler_interaction.add_entry(new_entry)
    
    #### update target cell on previous entry
    csv_handler_interaction.update_entry(len(csv_handler_interaction.read_entries())-2, {'Target_row': lastPressedCell_1[0], 'Target_col': lastPressedCell_1[1]})
    
    # predict next best steps
    # row_clues, column_clues = count_consecutive_cells(solutionGrid)
    # last_interactions = [lastPressedCell_1, lastPressedCell_2, lastPressedCell_3]
    # next_recommended_steps, process_explained = recommend_next_steps(no_next_steps=3, progressGrid=progressGrid, solutionGrid=solutionGrid, last_interactions=last_interactions, row_clues=row_clues, column_clues=column_clues)
    # # save process_explained into empty file
    # with open('data/nonogram_solver/process_explained.txt', 'w') as f:
    #     # empty file
    #     f.write("")
    #     for line in process_explained:
    #         f.write("%s\n" % line)
    # print("next_recommended_steps:: ", next_recommended_steps)
    
    return "Saved interaction data successfully!"

def fetch_messages_cached():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC')
    messages = cursor.fetchall()
    conn.close()
    messages = [{'user_message': message[1], 'ai_message': message[2], "timestamp": message[3]} for message in messages]
    return messages

def fetch_last_message_cached():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 1')
    last_message = cursor.fetchone()
    conn.close()
    last_message = {'user_message': last_message[1], 'ai_message': last_message[2], "timestamp": last_message[3]}
    return last_message

def fetch_last_5_messages_cached():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5')
    messages = cursor.fetchall()
    conn.close()
    messages = [{'user_message': message[1], 'ai_message': message[2], "timestamp": message[3]} for message in messages]
    return messages

def insert_new_message_cache(user_message, response_llm):
    # Add user message to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (user_message, ai_message) VALUES (?, ?)',
                (user_message, response_llm))
    conn.commit()
    
    # Fetch the new message
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 1')
    new_message = cursor.fetchone()
    conn.close()
    new_message = {'user_message': new_message[1], 'ai_message': new_message[2], "timestamp": new_message[3]}
    
    # Update the messages cache
    messages_cache.insert(0, (m for m in format_message(new_message)))

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
