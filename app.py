from flask import Flask, render_template, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
    callLLM_conclusive_hint,
    callLLM_meaning_hint
)                
# from old.azure_inference import callLLM_progress_checker                            # azure llm non chat
# from old.llm_chain_memory import callLLM                  # azure llm with langchain and llm chain memory (memory lost at every app restart)
from hf_inference import meaning_checker_hf                 # HF llm checking validity of user meaning
from data_collection import csv_handler_progress, csv_handler_meaning, csv_handler_game, csv_handler_interaction
from grid_difference_checker import count_consecutive_cells
from progress_tracking import (
    recommend_next_steps,
    track_hint_level,
    user_level_progress,
    get_interaction_id, increment_interaction_counter
)

app = Flask(__name__)

# Create a limiter with the default rate limit
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["7/second"]
)

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
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        hint_level INTEGER DEFAULT 0
    )
''')
conn.commit()
conn.close()

@app.route('/')
def index():
    """
    Route to the main page. Shows the chat interface with all history of messages.
    """
    global messages_cache
    messages = fetch_messages_cached()
    messages_cache = format_history(messages)
    return render_template('index.html', messages=messages, chatbot_name=chatbot_name)

@app.route('/send_message', methods=['POST'])
def send_message():
    """
    Route to send a message to the chatbot. Called by the form in the index.html file.
    When completed, redirects to the main page.
    """
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
    """
    Route called by Unity to check the meaning of the user's guess for the puzzle.
    """
    puzzle_meaning = request.form.get('puzzleMeaning')
    puzzle_meaning = json.loads(puzzle_meaning)
    user_guess = puzzle_meaning['user_guess']
    solution = puzzle_meaning['solution']
    username = puzzle_meaning['username']
    level = puzzle_meaning['level']
    
    # Call the Hugging Face model to check the meaning of the user's guess
    response, meaning_latency = meaning_checker_hf(user_guess, solution)
    
    # Save the data to the CSV database
    count_entries = len(csv_handler_meaning.read_entries())
    new_entry = {'id': count_entries, 'User': username, 'Level': level, 'Meaning': solution, 'Guess': user_guess, 'Approved': response, 'Model': 'HF Phi-3-mini-4k-instruct', 'Latency': meaning_latency, 'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    csv_handler_meaning.add_entry(new_entry)
    
    return response

@app.route('/check_puzzle_progress', methods=['POST'])
def check_puzzle_progress():
    """
    Route called by Unity to check the progress of the user in the puzzle and ask for a hint based on their progress.
    
    Based on the calculated progress difference, the hint level is updated as follows:
    - If the user is stuck at the same progress level (stagnant or negative progress), the hint level is increased.
    - If the user is making progress, the hint level is decreased.
    
    Hint levels hierarchy:
    0: general game rule hints  (return a general strategy or rule)
    1: directional hints        (return a row or column or area)
    2: conclusive hints         (return a correct cell)
    7: meaning hints            (return a riddle about what the grid represents)
    
    """
    puzzle_progress = request.form.get('puzzleProgress')
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

    ##### Track the hint level per user per level
    track_hint_level(username=username, level=level, progressGrid=cellStates, solutionGrid=solutionCellStates)
    print("user_level_progress:: ", user_level_progress)
    hint_level = user_level_progress[username]["hint_level"]
    # hint_level = 2 # for testing
    
    if hint_level > 0 and not completed:
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
            next_recommended_steps, _ = recommend_next_steps(no_next_steps=5, progressGrid=cellStates, solutionGrid=solutionCellStates, last_interactions=last_interactions, row_clues=row_clues, column_clues=column_clues)
    
    ##### Save the data to the CSV Progress database
    try:
        new_entry = {'id': hint_id, 'Hint_Level': hint_level, 'User': username, 'Level': level, 'Position': "-", 'Hint_Response': "-", 'Observation_Response': "-", 'Positioning_Response': "-", 'Position_Description': "-", 'Overall_Latency': "-", 'Hint_Latency': "-", 'Observation_Latency': "-", 'Position_Latency': "-", 'Hint_Model': "-", 'Observation_Model': "-", 'Position_Model': "-", 'Mistakes_per_Hint_Wrong': 0, 'Mistakes_per_Hint_Missing': 0, 'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        csv_handler_progress.add_entry(new_entry)
    except Exception as e:
        print("Error saving progress data:: ", e)
        
    ############################################## call LLM for response depending on the hint level
    messages_cache = format_history(fetch_last_5_messages_cached(hint_level))
    # print("messages_cache:: ", messages_cache)
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
    elif hint_level == 7:
        """Meaning hint"""
        response_llm = callLLM_meaning_hint(completed, levelMeaning, hint_id, messages_cache)
    ##### Request for the hint text to be verbalised (Text-to-Speech pipeline)
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
        insert_new_message_cache(message, response_llm, hint_level)
        
    # redirect('/')
    return response_llm

@app.route('/verbalise_hint', methods=['POST'])
def verbalise_hint():
    """
    Route called by Unity to verbalise the hint text.
    """
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
    """
    Route to clear all messages from the database history and the messages cache.
    """
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
    """
    Route called by Unity to save the game data to the CSV database. 
    Game data includes the user's progress in each level, the time taken to complete each level, the number of hints used, and the completion status of each level.
    """
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
@limiter.limit("1 per 0.2 seconds")
def record_interactions():
    """
    Route called by Unity to record the user's interactions with the Nonogram puzzle (clicks on each square of the puzzle).
    Records the user's last 3 interactions, the progress of the puzzle, and the predicted next best steps.
    
    Data saved is used to examine the accuracy of the Nonogram Solver's predictions for the next best steps. 
    """
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
    
    # Predict next best steps based on the last interactions
    row_clues, column_clues = count_consecutive_cells(solutionGrid)
    last_interactions = [lastPressedCell_1, lastPressedCell_2, lastPressedCell_3]
    next_recommended_steps, process_explained = recommend_next_steps(no_next_steps=5, progressGrid=progressGrid, solutionGrid=solutionGrid, last_interactions=last_interactions, row_clues=row_clues, column_clues=column_clues)
    
    interaction_counter = get_interaction_id()
    ##### Update ``Ground truth`` target cell on previous entry
    if interaction_counter > 1:
        try:
            csv_handler_interaction.update_entry(interaction_counter-1, {'Target_row': lastPressedCell_1[0], 'Target_col': lastPressedCell_1[1]})
        except Exception as e:
            print("Error updating the target cell on the previous entry:: ", e)
    
    ##### Save the data to the CSV Interaction database
    # each Cell_i is a list of  (Row, Column, Row Group Size, Column Group Size)
    new_entry = {'id': interaction_counter, 'User': username, 'Level': level, 'Cell_1': lastPressedCell_1, 'Cell_2': lastPressedCell_2, 'Cell_3': lastPressedCell_3, 'Grid': solutionGrid, 'Progress_Grid': progressGrid, 'Target_row': 'x', 'Target_col': 'y', 'Predicted_row': 0, 'Predicted_col': 0}    
    if recommend_next_steps != []:
        if next_recommended_steps != []:
            new_entry['Predicted_row'] = next_recommended_steps[0][0]
            new_entry['Predicted_col'] = next_recommended_steps[0][1]
    csv_handler_interaction.add_entry(new_entry)
    increment_interaction_counter()
    
    ##### Save process_explained into empty file
    with open('data/nonogram_solver/process_explained.txt', 'w') as f:
        # empty file
        f.write("")
        for line in process_explained:
            f.write("%s\n" % line)
    print("next_recommended_steps:: ", next_recommended_steps)
    
    return "Saved interaction data successfully!"

############################################################################################################
# Functions to interact with the SQLite database
############################################################################################################

def fetch_messages_cached():
    """
    Fetch all messages from the database and format them for the chat interface.
    """
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC')
    messages = cursor.fetchall()
    conn.close()
    messages = [{'user_message': message[1], 'ai_message': message[2], "timestamp": message[3]} for message in messages]
    return messages

def fetch_last_message_cached():
    """
    Fetch the last message from the database.
    """
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 1')
    last_message = cursor.fetchone()
    conn.close()
    last_message = {'user_message': last_message[1], 'ai_message': last_message[2], "timestamp": last_message[3]}
    return last_message

def fetch_last_5_messages_cached(hint_level):
    """
    Fetch the last 5 messages from the database that have the same hint level.
    """
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages WHERE hint_level = ? ORDER BY timestamp DESC LIMIT 5', (hint_level,))
    messages = cursor.fetchall()
    conn.close()
    messages = [{'user_message': message[1], 'ai_message': message[2], "timestamp": message[3]} for message in messages]
    return messages

def insert_new_message_cache(user_message, response_llm, hint_level):
    """
    Function to insert a new message into the database. Also updates the messages cache.
    Message format: (user message, llm response, hint level)
    """
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (user_message, ai_message, hint_level) VALUES (?, ?, ?)',
                (user_message, response_llm, hint_level))
    conn.commit()
    
    # Fetch the new message
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 1')
    new_message = cursor.fetchone()
    conn.close()
    new_message = {'user_message': new_message[1], 'ai_message': new_message[2], "timestamp": new_message[3]}
    
    # Update the messages cache
    messages_cache.insert(0, (m for m in format_message(new_message)))

def format_message(message):
    """
    Function to format the message to match the expected history format for the chat LLMs and the chat interface UI.
    """
    formatted_message = [
        {"role": "user", "content": message["user_message"]},
        {"role": "assistant", "content": message["ai_message"]},
    ]
    return formatted_message

def format_history(messages):
    """
    Function to format the a goup of messages to match the expected format.
    """
    formatted_messages = [m for message in messages for m in format_message(message)]
    return formatted_messages

if __name__ == '__main__':
    app.run(debug=True)
