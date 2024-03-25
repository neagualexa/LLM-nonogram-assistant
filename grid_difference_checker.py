def reformat_cellStates(cellStates, solutionCellStates):
    """
        At every | character, add a new line
    """
    cellStates = cellStates.split("|")
    solutionCellStates = solutionCellStates.split("|")
    # remove last newline
    cellStates = cellStates[:-1]
    solutionCellStates = solutionCellStates[:-1]
    width = len(cellStates[0])
    height = len(cellStates)
    
    formatted_grid = []
    formatted_Solution_grid = []
    for i, row in enumerate(cellStates):
        formatted_row = [cell for cell in row]
        formatted_grid.append(formatted_row)
    for i, row in enumerate(solutionCellStates):
        formatted_row = [cell for cell in row]
        formatted_Solution_grid.append(formatted_row)
        
    return formatted_grid, formatted_Solution_grid, width, height

def print_format_cellStates(cellStates, solutionCellStates):
    """
        At every | character, add a new line
    """
    
    formatted_grid = ["(     0 1 2 3 4 5 6 7 8 9)"]
    formatted_Solution_grid = ["(     1 2 3 4 5 6 7 8 9 10)"]

    for i, row in enumerate(cellStates):
        if i >= 9:
            formatted_row = f"[({i+1}) " + " ".join(row) + "]"
        else:
            formatted_row = f"[ ({i+1}) " + " ".join(row) + "]"
        formatted_grid.append(formatted_row)
    for i, row in enumerate(solutionCellStates):
        if i >= 9:
            formatted_row = f"[({i+1}) " + " ".join(row) + "]"
        else:
            formatted_row = f"[ ({i+1}) " + " ".join(row) + "]"
        formatted_Solution_grid.append(formatted_row)
        
    formatted_output = "\n".join(formatted_grid)
    formatted_solution = "\n".join(formatted_Solution_grid)
    return formatted_output, formatted_solution

def compare_grids(user_progress, solution):
    differences = {
        "wrong_selection": [],
        "missing_selection": []
    }
    for i in range(len(user_progress)):
        for j in range(len(user_progress[0])):
            if user_progress[i][j] != solution[i][j] and user_progress[i][j] == '1':
                differences["wrong_selection"].append((i+1, j+1)) # +1 to convert to 1-indexed
            if user_progress[i][j] != solution[i][j] and user_progress[i][j] == '0':
                differences["missing_selection"].append((i+1, j+1)) # +1 to convert to 1-indexed
    return differences
        
def generate_mistake_markers(differences):
    feedback_wrong = ""
    feedback_missing = ""
    for diff in differences["wrong_selection"]:
        feedback_wrong += f"Cell at row {diff[0]} and column {diff[1]} is incorrectly selected. \n"
    for diff in differences["missing_selection"]:
        feedback_missing += f"Cell at row {diff[0]} and column {diff[1]} is not selected. \n"
    return feedback_wrong, feedback_missing