from nonogram_solver import NonogramSolver
from grid_difference_checker import zeroToOneIndexed

user_level_progress = {}

def track_user_level_progress(username, level, progress):
    """
    Track the progress of the user for a specific level.
    """
    if username not in user_level_progress:
        user_level_progress[username] = {level: progress}
    elif level not in user_level_progress[username]:
        user_level_progress[username][level] = 0
    else:
        user_level_progress[username][level] = progress

def recommend_next_steps(no_next_steps, progressGrid, solutionGrid, last_interactions, row_clues, column_clues):
    # replace all 0s with -1s for empty cells
    prorgessGrid = [[-1 if cell == 0 else cell for cell in row] for row in progressGrid]
    solutionGrid = [[-1 if cell == 0 else cell for cell in row] for row in solutionGrid]
    solver = NonogramSolver(ROWS_VALUES=row_clues,COLS_VALUES=column_clues, PROGRESS_GRID=prorgessGrid, SOLUTION_GRID=solutionGrid, LAST_INTERACTIONS=last_interactions)#, savepath='data/nonogram_solver') # add a savepath to save the board at each iteration
    next_recommended_steps = solver.recommend_next_action(no_next_steps=no_next_steps)
    next_recommended_steps = zeroToOneIndexed(next_recommended_steps)       # convert to 1-indexed
    print("next_recommended_steps:: ", next_recommended_steps)
    
    return next_recommended_steps, solver.process_explained

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

