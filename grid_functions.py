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
    """
    Method to compare the user's progress with the solution grid and return the differences.
    1 indexed for human/LLM readability
    """
    differences = {
        "wrong_selection": [],
        "missing_selection": [],
        "expected_empty": []
    }
    filled = ['1', 1]
    empty  = ['0', 0]
    
    for i in range(len(user_progress)):
        for j in range(len(user_progress[0])):
            if user_progress[i][j] != solution[i][j] and (user_progress[i][j] in filled):
                # columns are x and rows are y; inverted row indices to have bottom left as (1,1)
                # differences["wrong_selection"].append((j+1, len(user_progress)-i)) # +1 to convert to 1-indexed
                differences["wrong_selection"].append((i+1, j+1))                   # cell is filled in the progress grid but should be empty in the solution grid (preserve row/column order: top left is (1,1))
            if user_progress[i][j] != solution[i][j] and (user_progress[i][j] in empty):
                # columns are x and rows are y; inverted row indices to have bottom left as (1,1)
                # differences["missing_selection"].append((j+1, len(user_progress)-i)) # +1 to convert to 1-indexed
                differences["missing_selection"].append((i+1, j+1))                 # cell is empty in the progress grid but should be filled in the solution grid (preserve row/column order: top left is (1,1))
            if solution[i][j] in empty:
                differences["expected_empty"].append((i+1, j+1))                    # cell is empty in the solution grid
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
    """
    Method to describe the position of a point in a grid with the top left corner as the origin.
    """
    row, col = position
    description = []

    # Check if the point is outside of the grid
    if col < 1 or col > width or row < 1 or row > height:
        return "Point is outside of the grid."

    # Corners
    if col == 1 and row == 1:
        description.append("top-left corner")
    elif col == 1 and row == height:
        description.append("bottom-left corner")
    elif col == width and row == 1:
        description.append("top-right corner")
    elif col == width and row == height:
        description.append("bottom-right corner")

    # Edges
    if col == 1:
        description.append("left edge")
    elif col == width:
        description.append("right edge")
    if row == 1:
        description.append("top edge")
    elif row == height:
        description.append("bottom edge")

    # Quadrants
    half_width = width // 2
    half_height = height // 2
    even_rows = height % 2 == 0
    even_cols = width % 2 == 0
    index_offset_row = 0 if even_rows else 1
    index_offset_col = 0 if even_cols else 1

    if col < half_width and row < half_height:
        description.append("top-left quadrant")
    elif col > half_width+index_offset_col and row < half_height:
        description.append("top-right quadrant")
    elif col < half_width and row > half_height+index_offset_row:
        description.append("bottom-left quadrant")
    elif col > half_width+index_offset_col and row > half_height+index_offset_row:
        description.append("bottom-right quadrant")

    # Rows and columns
    if row == half_height or row == half_height+index_offset_row:
        # description.append("middle rows")
        if col < half_width:
            description.append("middle left columns")
        elif col > half_width+index_offset_col:
            description.append("middle right columns")
        else:
            description.append("middle area")
    if col == half_width or col == half_width+index_offset_col:
        # description.append("middle columns")
        if row < half_height:
            description.append("middle top rows")
        elif row > half_height+index_offset_row:
            description.append("middle bottom rows")
        else:
            description.append("middle area")

    # Random choice from the collected descriptions
    return random.choice(description)

def decide_overall_area(locations_next_steps):
    """
    Method to decide the overall area described by the locations of the next steps.
    Take each location and decide the area it describes, then combine them into an overall area and prioritise the majority.
    """
    overall_area = {
        "top": 0,
        "bottom": 0,
        "left": 0,
        "right": 0,
        "middle": 0,
        "edge": 0,
        "corner": 0,
        "quadrant": 0,
        "rows": 0,
        "columns": 0
    }
    
    for location in locations_next_steps:
        # check for keywords in the location
        if "top" in location:
            overall_area["top"] += 1
        if "bottom" in location:
            overall_area["bottom"] += 1
        if "left" in location:
            overall_area["left"] += 1
        if "right" in location:
            overall_area["right"] += 1
        if "middle" in location:
            overall_area["middle"] += 1
        if "edge" in location:
            overall_area["edge"] += 1
        if "corner" in location:
            overall_area["corner"] += 1
        if "quadrant" in location:
            overall_area["quadrant"] += 1
        if "row" in location:
            overall_area["rows"] += 1
        if "column" in location:
            overall_area["columns"] += 1
            
    # Find the top two elements by their counts
    sorted_areas = sorted(overall_area.items(), key=lambda x: x[1], reverse=True)
    # get non-zero elements
    areas = [area for area, count in sorted_areas if count > 0]
    
    majority_area = ""
    area_components = (("",0),("",0),("",0))                      # (horizontal, vertical, locational) terms
    if areas[0] in("edge", "corner", "quadrant", "rows", "columns"):
        area_components = (area_components[0], area_components[1], (areas[0],1))
        areas.pop(0)
    for area in areas:
        if area in ("top", "bottom", "middle")                       and area_components[0][1] == 0:
            area_components = ((area,1), area_components[1], area_components[2])
        elif area in ("left", "right")                               and area_components[1][1] == 0:
            area_components = (area_components[0], (area,1), area_components[2])
        elif area in ("edge", "corner", "quadrant", "rows", "columns") and area_components[2][1] == 0:            # add onto until ending words are found
            area_components = (area_components[0], area_components[1], (area,1))
    
    majority_area = " ".join([component[0] for component in area_components])
    
    print(areas, area_components, majority_area)
    
    return majority_area

def count_consecutive_cells(grid):
    """
    Count the number of consecutive filled cells in each row and column of the grid. Forming the row and column clues for the puzzle.
    """
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

def get_cell_group_size(cell_states, row, column):
    """
    For a specific cell, find the size of the group of filled cells in the row and column it belongs to.
    """
    # Ensure dimensions
    if not (0 <= row < len(cell_states) and 0 <= column < len(cell_states[0])):
        raise IndexError("Row or column index is out of bounds.")
    
    row_group_size = find_group_size(cell_states, row, column, axis='row')
    column_group_size = find_group_size(cell_states, row, column, axis='column')

    return row_group_size, column_group_size


def find_group_size(cell_states, row, column, axis):
    """
    Calculate the size of the group of filled cells that the current cell belongs to.
    """
    if not cell_states[row][column]:
        return 0

    current_group = 0
    if axis == 'row':
        # Check if current cell is contiguous with the left neighbor
        if column > 0 and cell_states[row][column - 1]:
            return find_group_size(cell_states, row, column - 1, axis='row')
        
        # Traverse left and right
        col_copy = column
        while col_copy >= 0 and cell_states[row][col_copy]:
            current_group += 1
            col_copy -= 1
        col_copy = column + 1
        while col_copy < len(cell_states[0]) and cell_states[row][col_copy]:
            current_group += 1
            col_copy += 1

    elif axis == 'column':
        # Check if current cell is contiguous with the upper neighbor
        if row > 0 and cell_states[row - 1][column]:
            return find_group_size(cell_states, row - 1, column, axis='column')
        
        # Traverse up and down
        row_copy = row
        while row_copy >= 0 and cell_states[row_copy][column]:
            current_group += 1
            row_copy -= 1
        row_copy = row + 1
        while row_copy < len(cell_states) and cell_states[row_copy][column]:
            current_group += 1
            row_copy += 1

    # Remove the double-count of the initial cell
    return current_group - 1

def zeroToOneIndexed(cells):
    """
    Method to convert 0-indexed cells to 1-indexed cells
    """
    for i, cell in enumerate(cells):
        if not cell:                                            # check if cell is empty
            continue
        if type(cell) == int:                                   # check if cell is a number
            cells[i] = cell+1                                   # convert to 1-indexed
        elif len(cell) == 2:
            cells[i] = (cell[0]+1, cell[1]+1)                   # convert to 1-indexed
        elif len(cell) == 3:
            cells[i] = (cell[0]+1, cell[1]+1, cell[2])          # convert to 1-indexed, keep the third element as state of cell
        elif len(cell) == 4:
            cells[i] = (cell[0]+1, cell[1]+1, cell[2], cell[3]) # convert to 1-indexed
    return cells


#### OLD
# def describe_point_position_bottom_left(position, width, height):
#     """
#     Method to describe the position of a point in a grid, with the bottom left corner as the origin.
#     """
#     x, y = position
#     description = []
#     # 1-indexed
#     if x < 1 or x > width or y < 1 or y > height:
#         return "Point is outside of the grid."

#     # Define row subcases
#     if y >= height - 1:
#         row_desc = "top"                        # 10, 9
#     elif y >= height - 3:
#         row_desc = "middle top"                 # 8, 7
#     elif y >= height - 5: 
#         row_desc = "centre"                     # 6, 5
#     elif y >= 3:
#         row_desc = "middle bottom"              # 4, 3
#     else:
#         row_desc = "bottom"                     # 2, 1

#     # Define column subcases
#     if x >= width - 1:
#         col_desc = "right"
#     elif x >= width - 3:
#         col_desc = "middle right"
#     elif x >= width - 5:
#         col_desc = "centre"
#     elif x >= 4:
#         col_desc = "middle left"
#     else:
#         col_desc = "left"
        
#     if row_desc == "centre" and col_desc == "centre":
#         return "centre"
#     if row_desc == "centre":
#         return col_desc
#     if col_desc == "centre":
#         return row_desc
    
#     if "middle" in row_desc and "middle" in col_desc:
#         #remove middle from both
#         row_desc = row_desc.split(" ")[1]
#         col_desc = col_desc.split(" ")[1]
#         description.append( f"{row_desc} {col_desc}")
    
#     if row_desc in ("middle top", "top") and col_desc in ("middle right", "right"):
#         description.append( "top right corner")
#     if row_desc in ("middle top", "top") and col_desc in ("middle left", "left"):
#         description.append( "top left corner")
#     if row_desc in ("middle bottom", "bottom") and col_desc in ("middle right", "right"):
#         description.append( "bottom right corner")
#     if row_desc in ("middle bottom", "bottom") and col_desc in ("middle left", "left"):
#         description.append( "bottom left corner")

#     description.append( f"{row_desc} rows, {col_desc} columns")
#     description.append( f"{row_desc}, {col_desc} side")
#     description.append( f"{row_desc}, {col_desc} area")
    
#     return random.choice(description)