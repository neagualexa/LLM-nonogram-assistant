from nonogram_solver import NonogramSolver
from grid_functions import zeroToOneIndexed, compare_grids

user_level_progress = {}
interaction_counter = 0
levels_order = ["heart", "car", "toucan", "boat", "clock", "fish", "invertedcar"]
hint_level_duration = 1

def track_hint_level(username, level, progressGrid, solutionGrid, hint_id):
    """
    Track the hint level of the user based on the progress of the user for a specific level.
    Define the hint level based on the progress of the user over time.
    """
    # calculate progress of user and update the hint level accordingly
    progress = calculate_progress(progressGrid=progressGrid, solutionGrid=solutionGrid)
    track_user_level_progress(username, level, progress, hint_level_duration)
    define_hint_level(username, level, hint_level_duration, hint_id)

def calculate_progress(progressGrid, solutionGrid):
    """
    Calculate the progress by counting the number of cells that are correct in the progress grid and dividing to the total number of cells.
    
    Need to take into account the following:
        - current progress cells = supposed to be filled - supposed to be filled but empty + supposed to be empty - supposed to be empty but filled
        - correct cells = supposed to be empty + supposed to be filled = total cells
        - progress = current progress cells / total cells
           BUT, empty grid progress is equal to (supposed to be empty / total cells), instead of 0.0
           HENCE, distribute the progress on a 0.0 to 1.0 scale considering that (supposed to be empty / total cells) should be the minimum progress
                IF all cells completed wrongly, progress is negative as nb_wrong_cells &  nb_missing_cells are both max
    """
    progress = 0
    total_cells = len(solutionGrid) * len(solutionGrid[0])
    # use the compare_grids function to get the wrong cells and missing cells
    differences = compare_grids(progressGrid, solutionGrid)
    nb_wrong_cells = len(differences["wrong_selection"])            # supposed to be empty but filled
    nb_missing_cells = len(differences["missing_selection"])        # supposed to be filled but empty
    nb_expected_empty_cells = len(differences["expected_empty"])    # supposed to be empty

    # supposed to be empty + supposed to be filled = total cells = correct cells
    # supposed to be empty - supposed to be empty but filled + supposed to be filled - supposed to be filled but empty = current progress cells
    # total cells - wrong cells - missing cells = current progress cells
    progress = (total_cells - nb_wrong_cells - nb_missing_cells) / (total_cells) # BUT empty grid progress is equal to (supposed to be empty / total cells), instead of 0.0
    
    # distribute the progress on a 0.0 to 1.0 scale considering that (supposed to be empty / total cells) should be the minimum progress
    progress = (progress - nb_expected_empty_cells / total_cells) / (1 - nb_expected_empty_cells / total_cells)

    return progress

def track_user_level_progress(username, level, progress, hint_level_duration):
    """
    Track the progress of the user for a specific level.
    user_level_progress = {username: {  level: (previous progress, progress), 
                                        "hint_level": measure of hint conclusiveness, 
                                        "hint_session_counter": number of interactions before the hint level is changed
                            }}
    """
    if username not in user_level_progress:
        user_level_progress[username] = {level: {"progress": (0, progress), "hint_level": 0, "hint_session_counter": hint_level_duration}}      # (previous progress, progress)
    elif level not in user_level_progress[username]:
        user_level_progress[username][level] = {"progress": (0, progress), "hint_level": 0, "hint_session_counter": hint_level_duration}        # (previous progress, progress)
    
    # always update the progress of the user
    user_level_progress[username][level]["progress"] = (user_level_progress[username][level]["progress"][1], progress)
        
def define_hint_level(username, level, hint_level_duration, hint_id):
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
    curr_progress = user_level_progress[username][level]["progress"][1]
    prev_progress = user_level_progress[username][level]["progress"][0]
    hint_level = user_level_progress[username][level]["hint_level"]
    
    # player requesting their first hint and allow for first waiting loop
    if hint_id[:2] == "1_":
        if level in levels_order[:3]:
            """Start with General Hints for levels 1-3"""
            hint_level = 0      
        else:
            """Start with Directional Hints for levels 4-7"""
            hint_level = 1
        user_level_progress[username][level]["hint_level"] = hint_level
        user_level_progress[username][level]["hint_session_counter"] = 0
        return
    
    if curr_progress == 1:
        # if the user has completed the level, provide meaning hints
        user_level_progress[username][level]["hint_level"] = 7
        return
    elif curr_progress > 0.5:
        # if user returns to the level after a long time, skip wait loop, provide directional & conclusive hints from the start
        user_level_progress[username][level]["hint_session_counter"] = hint_level_duration
    
    ####### WAITING LOOP to wait for hint_level_duration interactions before changing hint level #######
    if user_level_progress[username][level]["hint_session_counter"] < hint_level_duration:
        # if the user is still in the same hint level session, provide hints of the same level until the session is over
        user_level_progress[username][level]["hint_session_counter"] += 1
        return
    
    user_level_progress[username][level]["hint_session_counter"] = 0
    progress_differece = curr_progress - prev_progress  # current progress - previous progress
    
    ####### Define the hint level based on the progress of the user over time #######
    if progress_differece <= 0:
        # if user is stuck at the same progress level (stagnant or negative progress)
        if curr_progress < 0.3:
            # at the beginning of the game, prioritise general game rule & directional hints
            user_level_progress[username][level]["hint_level"] = hint_level + 1 if hint_level < 1 else 1
        else:
            user_level_progress[username][level]["hint_level"] = hint_level + 1 if hint_level < 2 else 2
    else:
        # if user is making progress
        if curr_progress  > 0.5:
            # towards the end of the game, prioritise directional & conclusive hints
            user_level_progress[username][level]["hint_level"] = hint_level - 1 if hint_level > 1 else 1
        else:
            if level in levels_order[:3]:
                """General Hints for levels 1-3"""
                user_level_progress[username][level]["hint_level"] = hint_level - 1 if hint_level > 0 else 0
            else:
                user_level_progress[username][level]["hint_level"] = hint_level + 1 if hint_level < 1 else 1

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