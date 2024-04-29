from nonogram_solver import NonogramSolver
from grid_difference_checker import zeroToOneIndexed

user_level_progress = {}
interaction_counter = 0

def track_hint_level(username, level, progressGrid, solutionGrid):
    """
    Track the hint level of the user based on the progress of the user for a specific level.
    Define the hint level based on the progress of the user over time.
    """
    # calculate progress of user and update the hint level accordingly
    progress = calculate_progress(progressGrid=progressGrid, solutionGrid=solutionGrid)
    track_user_level_progress(username, level, progress)
    define_hint_level(username, level)

def calculate_progress(progressGrid, solutionGrid):
    """
    Calculate the progress by counting the number of cells that are correct in the progress grid and dividing to the total number of cells.
    """
    progress = 0
    no_cells_correct = 0   
    total_cells = len(progressGrid) * len(progressGrid[0])             
    for i in range(len(progressGrid)):
        for j in range(len(progressGrid[0])):
            if progressGrid[i][j] == solutionGrid[i][j]:
                no_cells_correct += 1
                
    progress = no_cells_correct / total_cells
    return progress

def track_user_level_progress(username, level, progress):
    """
    Track the progress of the user for a specific level.
    user_level_progress = {username: {  level: (previous progress, progress), 
                                        "hint_level": measure of hint conclusiveness, 
                                        "hint_session_counter": number of interactions before the hint level is changed
                            }}
    """
    if username not in user_level_progress:
        user_level_progress[username] = {level: (0, progress), "hint_level": 0, "hint_session_counter": 0}      # (previous progress, progress)
    elif level not in user_level_progress[username]:
        user_level_progress[username][level] = (0,0)                                                            # (previous progress, progress)
        user_level_progress[username]["hint_level"] = 0
        user_level_progress[username]["hint_session_counter"] = 0
    else:
        user_level_progress[username][level] = (user_level_progress[username][level][1], progress)
        
def define_hint_level(username, level, hint_level_duration=2):
    """
    Define the level of the hint based on the progress of the user over time. 
    Move through the hint levels based on the progress of the user over time (e.g. at the beginning; close to end game).
    {username: {level: (previous progress, progress)}}

    progress differece = a positive value indicates progress, a negative value indicates a decrease in progress, and 0 indicates stagnant progress.
    
    hint levels hierarchy:
    0: general game rule hints  (return a general strategy or rule)
    1: directional hints        (return a row or column or area)
    2: conclusive hints         (return a correct cell)
    7: meaning hints            (return a riddle about what the grid represents)
    
    hint_level_duration = a user will receive hints of the same level for a certain number of interactions before the hint level is changed.
    (nb hints given on same level = hint_level_duration + 1)
    """
    
    if user_level_progress[username][level][1] == 1:
        # if the user has completed the level, provide meaning hints
        user_level_progress[username]["hint_level"] = 7
        return
    
    if user_level_progress[username]["hint_session_counter"] < hint_level_duration:
        # if the user is still in the same hint level session, provide hints of the same level until the session is over
        user_level_progress[username]["hint_session_counter"] += 1
        return
    
    user_level_progress[username]["hint_session_counter"] = 0
    progress_differece = user_level_progress[username][level][1] - user_level_progress[username][level][0]  # current progress - previous progress
    
    if progress_differece <= 0:
        # if user is stuck at the same progress level (stagnant or negative progress)
        if user_level_progress[username][level][1] < 0.3:
            # at the beginning of the game, prioritise general game rule & directional hints
            user_level_progress[username]["hint_level"] = user_level_progress[username]["hint_level"] + 1 if user_level_progress[username]["hint_level"] < 1 else 1
        else:
            user_level_progress[username]["hint_level"] = user_level_progress[username]["hint_level"] + 1 if user_level_progress[username]["hint_level"] < 2 else 2
    else:
        # if user is making progress
        if user_level_progress[username][level][1]  > 0.8:
            # towards the end of the game, prioritise directional & conclusive hints
            user_level_progress[username]["hint_level"] = user_level_progress[username]["hint_level"] - 1 if user_level_progress[username]["hint_level"] > 1 else 1
        else:
            user_level_progress[username]["hint_level"] = user_level_progress[username]["hint_level"] - 1 if user_level_progress[username]["hint_level"] > 0 else 0

def recommend_next_steps(no_next_steps, progressGrid, solutionGrid, last_interactions, row_clues, column_clues):
    """
    Make a recommendation for the next steps to the user based on the progress grid and the solution grid.
    This will be used to provide hints of level 1 and 2 to the user.
    """
    # replace all 0s with -1s for empty cells
    prorgessGrid = [[-1 if cell == 0 else cell for cell in row] for row in progressGrid]
    solutionGrid = [[-1 if cell == 0 else cell for cell in row] for row in solutionGrid]
    solver = NonogramSolver(ROWS_VALUES=row_clues,COLS_VALUES=column_clues, PROGRESS_GRID=prorgessGrid, SOLUTION_GRID=solutionGrid, LAST_INTERACTIONS=last_interactions)#, savepath='data/nonogram_solver') # add a savepath to save the board at each iteration
    next_recommended_steps = solver.recommend_next_action(no_next_steps=no_next_steps)
    next_recommended_steps = zeroToOneIndexed(next_recommended_steps)                           # convert to 1-indexed
    next_recommended_steps = [(step[0], step[1], ("filled" if step[2] == 1 else "empty"))  for step in next_recommended_steps]   # convert value from int to descriptive string
    
    return next_recommended_steps, solver.process_explained

def get_interaction_id():
    """
    Get the unique identifier for the interaction.
    """
    global interaction_counter
    return interaction_counter

def increment_interaction_counter():
    """
    Increment the interaction counter.
    """
    global interaction_counter
    interaction_counter += 1