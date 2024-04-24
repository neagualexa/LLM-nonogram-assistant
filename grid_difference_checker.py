import random


def string_to_lists_grids(cellStates, solutionCellStates):
    """
        Split the cellStates and solutionCellStates strings into lists of lists
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
    
    # if indices:
    formatted_grid = ["(     0 1 2 3 4 5 6 7 8 9)"]
    formatted_Solution_grid = ["(     1 2 3 4 5 6 7 8 9 10)"]

    for i, row in enumerate(cellStates):
        if i >= 9:
            formatted_row = f"[({i+1}) " + " ".join(str(cell) for _, cell in enumerate(row)) + "]"
        else:
            formatted_row = f"[ ({i+1}) " + " ".join(str(cell) for _, cell in enumerate(row)) + "]"
        formatted_grid.append(formatted_row)
    for i, row in enumerate(solutionCellStates):
        if i >= 9:
            formatted_row = f"[({i+1}) " + " ".join(str(cell) for _, cell in enumerate(row)) + "]"
        else:
            formatted_row = f"[ ({i+1}) " + " ".join(str(cell) for _, cell in enumerate(row)) + "]"
        formatted_Solution_grid.append(formatted_row)
        
    formatted_output = "\n".join(formatted_grid)
    formatted_solution = "\n".join(formatted_Solution_grid)
    return formatted_output, formatted_solution
    
    # else:
    ### Too much information for the LLM to accurately understand, it confuses the hints with the actual grid
    #     # count consecutive cells and set the elements as indices of rows and columns
    #     row_counts, col_counts = count_consecutive_cells(solutionCellStates)
    #     str_row_counts = [str(r) for r in row_counts]
    #     str_col_counts = [str(c) for c in col_counts]
        
    #     for r, str_r in zip(row_counts, str_row_counts):
    #         if len(r) == 1:
    #             str_row_counts[str_row_counts.index(str_r)] += "      "
    #         elif len(r) == 2:
    #             str_row_counts[str_row_counts.index(str_r)] += "   "
                
    #     formatted_grid          = ["(         "+ " ".join(str(col_counts[i]) for i in range(len(cellStates[0]))) + ")"]
    #     formatted_Solution_grid = ["(         " + " ".join(str(col_counts[i]) for i in range(len(solutionCellStates[0]))) + ")"]
            
    #     for i, row in enumerate(cellStates):
    #         formatted_row = f"[{str_row_counts[i]} " + " ".join(row) + "]"
    #         formatted_grid.append(formatted_row)
    #     for i, row in enumerate(solutionCellStates):
    #         formatted_row = f"[{str_row_counts[i]} " + " ".join(row) + "]"
    #         formatted_Solution_grid.append(formatted_row)
        
    #     return formatted_grid, formatted_Solution_grid

def compare_grids(user_progress, solution):
    differences = {
        "wrong_selection": [],
        "missing_selection": []
    }
    filled = ['1', 1]
    empty  = ['0', 0]
    
    for i in range(len(user_progress)):
        for j in range(len(user_progress[0])):
            if user_progress[i][j] != solution[i][j] and (user_progress[i][j] in filled):
                # columns are x and rows are y; inverted row indices to have bottom left as (1,1)
                differences["wrong_selection"].append((j+1, len(user_progress)-i)) # +1 to convert to 1-indexed
            if user_progress[i][j] != solution[i][j] and (user_progress[i][j] in empty):
                # columns are x and rows are y; inverted row indices to have bottom left as (1,1)
                differences["missing_selection"].append((j+1, len(user_progress)-i)) # +1 to convert to 1-indexed
    return differences

def random_element(wrong_selections, missing_selections):
    # choose one of the lists randomly and return one of its elements at random
    if not wrong_selections:
        return random.choice(missing_selections)
    if not missing_selections:
        return random.choice(wrong_selections)
    
    random_list = random.choice([wrong_selections, missing_selections])
    random_element = random.choice(random_list)
    return random_element
        
def generate_mistake_markers(differences):
    feedback_wrong = ""
    feedback_missing = ""
    for diff in differences["wrong_selection"]:
        feedback_wrong += f"Cell at row {diff[0]} and column {diff[1]} is incorrectly selected. \n"
    for diff in differences["missing_selection"]:
        feedback_missing += f"Cell at row {diff[0]} and column {diff[1]} is not selected. \n"
    return feedback_wrong, feedback_missing

def describe_point_position(position, width, height):
    x, y = position
    description = []
    # 1-indexed
    if x < 1 or x > width or y < 1 or y > height:
        return "Point is outside of the grid."

    # Define row subcases
    if y >= height - 1:
        row_desc = "top"                        # 10, 9
    elif y >= height - 3:
        row_desc = "middle top"                 # 8, 7
    elif y >= height - 5: 
        row_desc = "centre"                     # 6, 5
    elif y >= 3:
        row_desc = "middle bottom"              # 4, 3
    else:
        row_desc = "bottom"                     # 2, 1

    # Define column subcases
    if x >= width - 1:
        col_desc = "right"
    elif x >= width - 3:
        col_desc = "middle right"
    elif x >= width - 5:
        col_desc = "centre"
    elif x >= 4:
        col_desc = "middle left"
    else:
        col_desc = "left"
        
    if row_desc == "centre" and col_desc == "centre":
        return "centre"
    if row_desc == "centre":
        return col_desc
    if col_desc == "centre":
        return row_desc
    
    if "middle" in row_desc and "middle" in col_desc:
        #remove middle from both
        row_desc = row_desc.split(" ")[1]
        col_desc = col_desc.split(" ")[1]
        description.append( f"{row_desc} {col_desc}")
    
    if row_desc in ("middle top", "top") and col_desc in ("middle right", "right"):
        description.append( "top right corner")
    if row_desc in ("middle top", "top") and col_desc in ("middle left", "left"):
        description.append( "top left corner")
    if row_desc in ("middle bottom", "bottom") and col_desc in ("middle right", "right"):
        description.append( "bottom right corner")
    if row_desc in ("middle bottom", "bottom") and col_desc in ("middle left", "left"):
        description.append( "bottom left corner")

    description.append( f"{row_desc} rows, {col_desc} columns")
    description.append( f"{row_desc}, {col_desc} side")
    description.append( f"{row_desc}, {col_desc} area")
    # description.append( f"{row_desc}")
    # description.append( f"{col_desc}")
    
    return random.choice(description)

def count_consecutive_cells(grid):
    row_counts = []
    col_counts = []

    def calculate_group_counts(array):
        group_counts = []
        count = 0
        for cell in array:
            if cell == '1' or cell == 1:
                count += 1
            elif count > 0:
                group_counts.append(count)
                count = 0
                
        if count > 0:
            group_counts.append(count)
        elif group_counts == []:
            group_counts.append(count)
        return group_counts

    # Count consecutive 1s in each row
    for row in grid:
        row_counts.append(calculate_group_counts(row))

    # Transpose the grid to count consecutive 1s in each column
    transposed_grid = [[grid[j][i] for j in range(len(grid))] for i in range(len(grid[0]))]

    # Count consecutive 1s in each column (same logic as for rows)
    for col in transposed_grid:
        col_counts.append(calculate_group_counts(col))

    return row_counts, col_counts


def zeroToOneIndexed(cells):
    for i, cell in enumerate(cells):
        # check if cell is empty
        if not cell:
            continue
        cells[i] = (cell[0]+1, cell[1]+1, cell[2], cell[3]) # convert to 1-indexed
    return cells