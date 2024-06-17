# Nonogram solver/validator solution adapted from Hennie de Harder's article "Solving Nonograms with 120 Lines of Code" 
# (https://towardsdatascience.com/solving-nonograms-with-120-lines-of-code-a7c6e0f627e4) [published: Jul 1, 2022]
# Credits of original code to: Hennie de Harder
# NOTES:
#       for nonograms with only one solution
#       0 = null cell, 1 = filled cell, -1 = empty cell
#       0 indexed grid and constraints
#       puzzle is being completed from left to right and top to bottom

import os, time
from itertools import combinations
import numpy as np 
import matplotlib.pyplot as plt 
from IPython.display import clear_output

class NonogramSolver:
    def __init__(self, ROWS_VALUES, COLS_VALUES, PROGRESS_GRID, SOLUTION_GRID, LAST_INTERACTIONS, savepath=''):
        self.ROWS_VALUES = ROWS_VALUES
        self.no_of_rows = len(ROWS_VALUES)
        # self.rows_changed = [0] * self.no_of_rows
        self.rows_done = [0] * self.no_of_rows      # 0 = not done, 1 = done

        self.COLS_VALUES = COLS_VALUES
        self.no_of_cols = len(COLS_VALUES)
        # self.cols_changed = [0] * self.no_of_cols
        self.cols_done = [0] * self.no_of_cols      # 0 = not done, 1 = done

        self.solved = False 
        self.shape = (self.no_of_rows, self.no_of_cols)
        self.board = [[0 for c in range(self.no_of_cols)] for r in range(self.no_of_rows)]
        self.progress_grid = PROGRESS_GRID
        self.solution_grid = SOLUTION_GRID
        self.last_interactions = LAST_INTERACTIONS
        self.priority_lines = {}
        self.process_explained = []
        self.total_linewide_steps = 0
        
        # tracking progress for benchmarking bot
        self.progress = 0
        self.prev_progress = 0
        
        self.savepath = savepath
        if self.savepath != '': self.n = 0

    def solve(self):
        """
        Method that solves the nonogram puzzle.
        Keep track of the number of steps taken to solve the puzzle.
        """
        # step 1: Defining all possible solutions for every row and col (indepenedently of the other rows and cols)
        self.rows_possibilities = self.create_possibilities(self.ROWS_VALUES, self.no_of_cols)
        self.cols_possibilities = self.create_possibilities(self.COLS_VALUES, self.no_of_rows)
        
        while not self.solved:
            # step 2: Order indici by lowest (start with the rows and cols with the lowest number of possibilities -> most likely to have larger clues)
            self.lowest_rows = self.select_index_not_done(self.rows_possibilities, 1)                   # get the rows with the lowest number of possibilities
            self.lowest_cols = self.select_index_not_done(self.cols_possibilities, 0)                   # get the cols with the lowest number of possibilities
            self.lowest = sorted(self.lowest_rows + self.lowest_cols, key=lambda element: element[1])   # sort by lowest number of possibilities

            # step 3: Get only zeroes or only ones of lowest possibility (rows or cols with least possibilities of combinations of completions)
            for ind1, _, row_ind in self.lowest:
                """ `row_ind` is a boolean that indicates whether the current context is a row (True) or a column (False). """
                if not self.check_done(row_ind, ind1):
                    # if the row or column is not done yet, get the possibilities for the row or column
                    if row_ind: values = self.rows_possibilities[ind1]  # get the possibilities for the row
                    else:       values = self.cols_possibilities[ind1]  # get the possibilities for the column
                    same_ind = self.get_only_one_option(values)         # get the cells that have only one possible value across all possibilities in the line   
                    
                    for ind2, val in same_ind:
                        # for each cell with only one possible position in line, update the board with the value
                        
                        # get the row and column index based on the row_ind boolean (whether it is a row or a column)
                        if row_ind: ri, ci = ind1, ind2                 # if row
                        else:       ri, ci = ind2, ind1                 # if column
                        
                        # update the board only for the cell that is gray (null cell)
                        if self.board[ri][ci] == 0:
                            self.board[ri][ci] = val                # update the cell with the value
                            if row_ind: self.cols_possibilities[ci] = self.remove_possibilities(self.cols_possibilities[ci], ri, val)   # remove the possibilities for the column depending on the value of the cell
                            else:       self.rows_possibilities[ri] = self.remove_possibilities(self.rows_possibilities[ri], ci, val)   # remove the possibilities for the row depending on the value of the cell
                            # clear_output(wait=True)                              
                            # self.display_board_temporary()
                            if self.savepath != '':
                                self.save_board()
                                self.n += 1
                    self.total_linewide_steps += 1                      # keep track of number of steps per all lines
                    self.update_done(row_ind, ind1)                 # update the rows_done or cols_done list when a row or column is completed
            self.check_solved()                                     # check if the puzzle is solved
        if self.solved: self.solution_grid = self.board.copy()      # set the solution grid to the board when the puzzle is solved
        
    def recommend_next_action(self, no_next_steps = 1, whole_line=False, random_line=False, random_linewide_step=None):
        """
        Method that recommends the next cell to fill in the nonogram puzzle based on the current grid progress state.
        The method also considers the last interactions with the grid to prioritize the rows and columns that were last interacted with. (including the rows and columns right next to the last interacted row or column)
        Always look in the vicinity of the last interaction.
        
        Set no_next_steps to 100 to get all the recommended next steps for 10x10 nonogram puzzle.
        
        Set whole_line to True to return the recommended next steps (definite cells) that were possible to be filled in that row or column (the no of steps will differ based on the number of definite cells in that row or column at the given moment)
       
        Set random_line to True to return a random linewide move (a random group of definite cells in a row or column). Which linewide move is returned is defined by the integer random_linewide_step.
        """
        next_recommended_steps = []
        self.process_explained = [] # reset the process explained
        
        # step 1: Set the board to be the progress grid
        self.board = self.progress_grid
        
        # step 2: Find all the differences between the progress grid and the solution grid and nullify the mistakes in the board (set mistake cells to 0 (null cell))
        self.nullify_mistakes(self.progress_grid, self.solution_grid)
        # step 2.2: Set all the empty cells (-1) in the grid to 0 (null cell) to allow for possibilities to be generated
        self.board = [[0 if cell == -1 else cell for cell in row] for row in self.board]
        
        # step 3: Defining all possible solutions for every row and col
        self.rows_possibilities = self.create_possibilities(self.ROWS_VALUES, self.no_of_cols)
        self.cols_possibilities = self.create_possibilities(self.COLS_VALUES, self.no_of_rows)
        
        # step 4: remove the possibilities that do not match the value of the cells correctly completed in the grid (impossible solutions for other rows or columns)
        for i in range(self.no_of_rows):
            for j in range(self.no_of_cols):
                if self.board[i][j] != 0:
                    self.rows_possibilities[i] = self.remove_possibilities(self.rows_possibilities[i], j, self.board[i][j])
                    self.cols_possibilities[j] = self.remove_possibilities(self.cols_possibilities[j], i, self.board[i][j])
        
        #step 5: Solve the puzzle with the remaining possibilities
        while not self.solved:
            # step 5.1: Order indici by priority and lowest (start with the rows and cols with the lowest number of possibilities -> most likely to have larger clues)
            self.lowest_rows = self.select_index_not_done(self.rows_possibilities, 1)
            self.lowest_cols = self.select_index_not_done(self.cols_possibilities, 0)
            # step 5.1.1: First sort the rows and cols by the lowest number of possibilities
            self.lowest = sorted(self.lowest_rows + self.lowest_cols, key=lambda element: element[1])

            if self.last_interactions != []:
                # step 5.1.2: Get the priority rows and columns based on the last interactions with the grid (also consider the rows and columns right next to the last interacted row or column)
                self.priority_lines = self.get_priority_lines(self.last_interactions)       # priority used to sort the rows and columns in custom_sort_priority
                self.process_explained.append("- user interacted last with: " + str(self.last_interactions) + "\n")
                # Step 5.1.3: Then re-sort the combined list (of rows and columns) by priority of interaction
                self.priority_lowest = sorted(self.lowest, key=self.custom_sort_priority)
            else:
                self.priority_lowest = self.lowest

            # step 5.2: Get only zeroes or only ones of lowest possibility (rows or cols with least possibilities of combinations of completions)
            for ind1, _, row_ind in self.priority_lowest:
                if not self.check_done(row_ind, ind1):
                    self.process_explained.append("-- \talgo pass through the rows or cols with least possibilities of combinations of completions & are not done yet")
                    self.process_explained.append(f"-- \tcurrent {'row' if row_ind else 'column'} {ind1}.")
                    # If the row or column is not done yet, get the possibilities for the row or column
                    if row_ind: values = self.rows_possibilities[ind1]
                    else:       values = self.cols_possibilities[ind1]
                    # Then identifiy which cells in a set of possiblities of row/column patterns have a consistent value across all possibilities, and return those cells. (DEFINITE CELLS)
                    same_ind = self.get_only_one_option(values)
                    self.process_explained.append(f"-- \tget the cells that have only one possible value across all possibilities in the {'row' if row_ind else 'column'} {ind1}: ({'column' if row_ind else 'row'}, value) {same_ind}.")
                    
                    for ind2, val in same_ind:
                        # For each cell with only one possible position in row/column, update the board with the value
                        if row_ind: ri, ci = ind1, ind2
                        else:       ri, ci = ind2, ind1 
                        if self.board[ri][ci] == 0:
                            # Check if the cell is not assigned a state -> only update if the cell is an null cell
                            # print(f'Inconsistency in cell row: {ri}, col: {ci}, current: {self.board[ri][ci]} should be val: {val}!')
                            if not (self.board[ri][ci] == 0 and val == -1 and self.progress_grid[ri][ci] == -1):
                                # Ignore the cells that should be empty, do not recommend the user to keep a cell empty
                                self.process_explained.append(f">--- \tCell on row: {ri}, col: {ci} is a null cell with one possible value accross all combinations of the {'row' if row_ind else 'column'}, so update the cell with the value {val} ({'filled' if val == 1 else 'empty' }). Recommend the user to change the cell state!!!!!")
                                # print(f'Recommended next cell is: row: {ri}, col: {ci}, val: {val} [0 indexed]')
                                if no_next_steps > 0:
                                    if random_linewide_step != None: 
                                        if random_linewide_step > 0: continue
                                    next_recommended_steps.append((ri, ci, val))
                                    if not whole_line and not random_line: no_next_steps -= 1
                                
                                if no_next_steps == 0 and not whole_line and not random_line:
                                    return next_recommended_steps, _, _
                                
                            self.board[ri][ci] = val
                            # If loop not broken, then a cell was completed in that row/column, so remove the other possibilities that do not match that specific cell's state at its supposed location
                            if row_ind: self.cols_possibilities[ci] = self.remove_possibilities(self.cols_possibilities[ci], ri, val)
                            else:       self.rows_possibilities[ri] = self.remove_possibilities(self.rows_possibilities[ri], ci, val)
                            self.process_explained.append(f"--- \tRemove the possibilities that do not match the value of the cell at the given location (row: {ri}, col: {ci}, val: {val})(remove impossible solutions for other rows or columns).")
                    
                    # if whole_line is set to true, then return the recommended next steps (definite cells) that were possible to be filled in that row or column & the number of combinations of completions for that row or column
                    line_index = ("Row ",ind1) if row_ind else ("Column ",ind1)
                    # print("Possible combinations of completions for the", line_index, ":", (values))
                    if whole_line and len(next_recommended_steps) != 0: return next_recommended_steps, len(values), line_index                      # do not return the next steps for a completed line (e.g. next_recommended_steps = [])
                    if random_line and random_linewide_step != None:
                        random_linewide_step -= 1
                        if random_linewide_step <= 0 and len(next_recommended_steps) != 0: return next_recommended_steps, len(values), line_index   # return a random linewide move                                     
                    # A new row/column has been fully completed, so mark them as done
                    self.update_done(row_ind, ind1)
                    self.process_explained.append(f"-- \tUpdate that {'row' if row_ind else 'column' } {ind1} is completed with all cells.\n")
            # check if nonogram grid is completed
            self.check_solved()
            self.process_explained.append(f"\n-- \tCheck if the nonogram puzzle is solved. {self.solved}")
        return next_recommended_steps, _, _ # No recommended next step as the grid is solved
    
    def nullify_mistakes(self, progress_grid, solution_grid):
        """
        Method that finds the differences between the progress grid and the solution grid and nullifies the mistakes in the board by setting the cell to 0 (null cell).
        Hence, those cell will be reconsidered in forming the line filling possibilities.
        """
        differences = self.compare_grids(progress_grid, solution_grid)
        
        for diff in differences["wrong_selection"]:
            self.board[diff[0]][diff[1]] = 0        # set the cell to 0 (null cell) (0 indexed)
        for diff in differences["missing_selection"]:
            self.board[diff[0]][diff[1]] = 0        # set the cell to 0 (null cell) (0 indexed)
            
    def compare_grids(self, progress, solution):
        """
        Method that compares the progress grid with the solution grid and returns the differences between the two grids.
        
        differences: dictionary with two keys: 'wrong_selection' and 'missing_selection'
        """
        differences = {
            "wrong_selection": [],
            "missing_selection": []
        }
        for i in range(len(progress)):
            for j in range(len(progress[0])):
                if progress[i][j] != solution[i][j] and (progress[i][j] == 1):
                    differences["wrong_selection"].append((i, j))                   # cell is filled in the progress grid but should be empty in the solution grid
                if progress[i][j] != solution[i][j] and (progress[i][j] == -1 or progress[i][j] == 0):
                    differences["missing_selection"].append((i, j))                 # cell is empty in the progress grid but should be filled in the solution grid
        return differences
    
    def create_possibilities(self, values, no_of_other):
        """
        Public method that generates all possible sequences of filled and empty cells for each row or column in a nonogram puzzle, 
        given the sequence of clues and the total number of cells.
        
        values:         list of lists of integers (ROW_VALUES or COLS_VALUES)
        no_of_other:    integer (no_of_cols or no_of_rows)
        
        possibilities:  list of lists of lists of integers => all possible solutions for all rows or columns
        """
        possibilities = []
        
        for v in values:                            # iterate over the values of each row or column
            groups = len(v)                         # calculate the number of groups of filled cells on either row or column
            no_empty = no_of_other-sum(v)-groups+1  # calculate the number of empty cells
            ones = [[1]*x for x in v]               # create a list of lists of 1s of size of the values on either row or column
            res = self._create_possibilities(no_empty, groups, ones)    # generate all possible combinations of filled and empty cells on line
            possibilities.append(res)  
        
        return possibilities

    def _create_possibilities(self, n_empty, groups, ones):
        """
        Helper function used internally by the create_possibilities function to generate combinations of filled and empty cells 
        based on the number of groups and empty cells for one row or column.
        
        n_empty:    integer (no_empty)
        groups:     integer (groups)
        ones:       list of lists of integers (ones)
        
        res_opts:   list of lists of integers (res_opt: list of integers) => all possible solutions for one row or column
        """
        res_opts = []
        for p in combinations(range(groups+n_empty), groups):   # generate all possible combinations of filled and empty cells on line
            selected = [-1]*(groups+n_empty)                    # create a list of -1s of size of the values on either row or column
            ones_idx = 0
            for val in p:
                selected[val] = ones_idx                        # replace the -1s with the values of the filled cells
                ones_idx += 1                                   # increment the index of the filled cells
            res_opt = [ones[val]+[-1] if val > -1 else [-1] for val in selected]    # replace the -1s with the values of the filled cells
            res_opt = [item for sublist in res_opt for item in sublist][:-1]        # flatten the list of lists, remove the value at the end (only )
            res_opts.append(res_opt)                                                # append the result to the list of possibilities for that one row or column
        return res_opts
    
    def remove_possibilities(self, possibilities, i, val):
        """
        Public method that removes the possibilities that do not match the value of the cell at the given index (impossible solutions for other rows or columns).
        """
        return [p for p in possibilities if p[i] == val]
    
    def select_index_not_done(self, possibilities, row_ind):
        """
        Public method that selects the indices of the rows or columns that have not been completed yet.
        
        row_ind: boolean (True for row, False for column)
        (i, n, row_ind): tuple of integers (index, number of possibilities, row or column index boolean)
        """
        s = [len(i) for i in possibilities]
        if row_ind:
            return [(i, n, row_ind) for i, n in enumerate(s) if self.rows_done[i] == 0]
        else:
            return [(i, n, row_ind) for i, n in enumerate(s) if self.cols_done[i] == 0]

    def get_priority_lines(self, last_interactions):
        """
        Method that returns the priority rows and columns based on the last interactions with the grid.
        
        Priority means that the solver will first try to solve the rows and columns that were last interacted with.
        Also introduce the rows and columns that are right next to the last interacted row or column.
        
        Also, check for overall direction of the user's movement, is it mainly horizontal or vertical?
        """
        priority_lines = {
            "main direction": (), # (row or column index, row index boolean) 
            "rows": [],
            "cols": []
        }
        
        # Check for the main direction of the user's movement (difference between the last two interactions)
        length_non_None = len([i for i in last_interactions if i != None])  # length of the last interactions if they are not None
        if length_non_None > 1:
            row_diff = last_interactions[0][0] - last_interactions[1][0]
            col_diff = last_interactions[0][1] - last_interactions[1][1]
            if row_diff == 0: priority_lines["main direction"] = (last_interactions[0][0], 1)
            elif col_diff == 0: priority_lines["main direction"] = (last_interactions[0][1], 0)
            
        # Add the interacted row or column and their neighbours to the priority list
        for interaction in last_interactions:
            if interaction == None: continue
            if not interaction[0] in priority_lines["rows"]:
                priority_lines["rows"].append(interaction[0])
                if interaction[0] + 1 <= self.no_of_rows: priority_lines["rows"].append(interaction[0] + 1)
                if interaction[0] - 1 >= 0:               priority_lines["rows"].append(interaction[0] - 1)
            if not interaction[1] in priority_lines["cols"]:
                priority_lines["cols"].append(interaction[1])
                if interaction[1] + 1 <= self.no_of_cols: priority_lines["cols"].append(interaction[1] + 1)
                if interaction[1] - 1 >= 0:               priority_lines["cols"].append(interaction[1] - 1)
                
        return priority_lines
        
    def custom_sort_priority(self, item):
        """
        Method that is used by `sorted()` as a `key` to sort the list of rows and columns by priority of interaction.
        The sorting will first prioritize elements with the lowest number of possibilities. 
        If there are multiple elements with the same number of possibilities, it will then prioritize based on the custom priority.
        
        (i, n, row_ind): tuple of integers (index, number of possibilities, row or column index boolean)
        """
        i, n, row_ind = item
        priority = 2            # Default priority (2 means not in the top list)
        
        # Assign priority if it's in the priority list; 0 means first priority; 1 means it is in the top list (no priority between other top list elements)
        if (i, row_ind) == self.priority_lines["main direction"]:
            priority = 0
        elif (row_ind) and i in self.priority_lines["rows"]:
            priority = 1
        elif (not row_ind) and i in self.priority_lines["cols"]:
            priority = 1
            
        return (n, priority) # order of priority: number of possibilities, priority

    def get_only_one_option(self, values):
        """
        Function identifies which cells in a set of possible nonogram row or column patterns have a consistent value across all possibilities. 
        These consistent values indicate places where there is only one possible solution for that cell, which can be filled into the nonogram grid.
        """
        return [(n, np.unique(i)[0]) for n, i in enumerate(np.array(values).T) if len(np.unique(i)) == 1]
    
    def update_done(self, row_ind, idx):
        """
        Public method that updates the rows_done or cols_done list when a row or column is completed.
        0 = not done, 1 = done
        """
        if row_ind: vals = self.board[idx]
        else: vals = [row[idx] for row in self.board]
        # if no null cells in the row or column, then the row or column is done
        if 0 not in vals:
            if row_ind: self.rows_done[idx] = 1
            else: self.cols_done[idx] = 1 

    def check_done(self, row_ind, idx):
        """
        Public method that checks if row or column `idx` is done.
        
        row_ind: boolean (True for row, False for column)
        rows_done: list of integers (0 = not done, 1 = done)
        cols_done: list of integers (0 = not done, 1 = done)
        """
        if row_ind: return self.rows_done[idx]
        else: return self.cols_done[idx]

    def check_solved(self):
        """
        Method that checks if the nonogram puzzle is solved.
        Checks if all rows and columns are completed.
        """
        if 0 not in self.rows_done and 0 not in self.cols_done:
            self.solved = True
            
    def check_with_solution(self):
        """
        Method that checks if the progress grid is the same as the solution grid.
        """
        self.solved = self.board == self.solution_grid
            
    def display_board_temporary(self):
        clear_output(wait=True) 
        plt.imshow(self.board, cmap='Greys')
        plt.axis('off')
        # close the plot to continue
        plt.show(block=False)
        plt.pause(0.2)
        plt.close()
        
    def display_board(self):
        clear_output(wait=True) 
        plt.imshow(self.board, cmap='Greys')
        plt.axis('off')
        plt.show()

    def save_board(self, increase_size=20):
        """
        Save the board as an image file.
        """
        name = f'0000000{str(self.n)}'[-8:]
        increased_board = np.zeros(np.array((self.no_of_rows, self.no_of_cols)) * increase_size)
        for j in range(self.no_of_rows):
            for k in range(self.no_of_cols):
                increased_board[j * increase_size : (j+1) * increase_size, k * increase_size : (k+1) * increase_size] = self.board[j][k]
        plt.imsave(os.path.join(self.savepath, f'{name}.jpeg'), increased_board, cmap='Greys', dpi=1000)


    #########
    ######### BENCHMARKING BOT #########
    ######### Simulates a Human 
    #                   - making mistakes while completing the puzzle (misinterpreting the clues) and 
    #                   - not understanding the hint provided(ignoring the recommended best next steps).
    #         Probabilities are set for the bot to make mistakes and ignore the hint.
    #########
    
    def solve_with_mistakes(self, prob_mistake=1, prob_respect_recommendation=1):
        """
        Method that tries to solve a nonogram puzzle by following the `solve` method, but with a probability of making a mistake
        (mistake = completing a cell that is not unique throughout all the combinations of the line (in `get_only_one_option` also return a non unique cell)).
        When a mistake is made, the solver will ask for the recommendation of the next action to take from `recommended_next_action` method.
        
        Parameters for describing the process:
            - probability of making a mistake/non optimal step
            - probability of respecting the recommended next steps
        """
        # step 1: Defining all possible solutions for every row and col (indepenedently of the other rows and cols)
        self.rows_possibilities = self.create_possibilities(self.ROWS_VALUES, self.no_of_cols)
        self.cols_possibilities = self.create_possibilities(self.COLS_VALUES, self.no_of_rows)
        
        while not self.solved:
            # step 2: Order indici by lowest (start with the rows and cols with the lowest number of possibilities -> most likely to have larger clues)
            self.lowest_rows = self.select_index_not_done(self.rows_possibilities, 1)                   # get the rows with the lowest number of possibilities
            self.lowest_cols = self.select_index_not_done(self.cols_possibilities, 0)                   # get the cols with the lowest number of possibilities
            self.lowest = sorted(self.lowest_rows + self.lowest_cols, key=lambda element: element[1])   # sort by lowest number of possibilities

            # step 3: Get only zeroes or only ones of lowest possibility (rows or cols with least possibilities of combinations of completions)
            for ind1, _, row_ind in self.lowest:
                if self.solved:
                    break
                """ `row_ind` is a boolean that indicates whether the current context is a row (True) or a column (False). """
                if not self.check_done(row_ind, ind1):
                    # if the row or column is not done yet, get the possibilities for the row or column
                    if row_ind: values = self.rows_possibilities[ind1]  # get the possibilities for the row
                    else:       values = self.cols_possibilities[ind1]  # get the possibilities for the column
                    same_ind = self.get_only_one_option(values)         # get the cells that have only one possible value across all possibilities in the line   
                    
                    """ For a prob_mistake probability, make a mistake by also considering a non unique cell """
                    mistake_ind = self.add_nonunique_option(same_ind, row_ind) if np.random.rand() < prob_mistake else same_ind
                    # print(f"unique cells and one mistake on `{'row' if row_ind else 'column'} {ind1}`: len(same_ind)={len(same_ind)} -> len(mistake)={len(mistake_ind)}:{mistake_ind}")
                    
                    for ind2, val in mistake_ind:
                        if self.solved:
                            break
                        # for each cell with only one possible position in line, update the board with the value
                        
                        # get the row and column index based on the row_ind boolean (whether it is a row or a column)
                        if row_ind: ri, ci = ind1, ind2                 # if row
                        else:       ri, ci = ind2, ind1                 # if column
                        
                        # update the board only for the cell that is gray (null cell)
                        if self.board[ri][ci] == 0:
                            self.board[ri][ci] = val                # update the cell with the value
                            # print(f"update the cell {ri, ci} -> {row_ind} with the value {val}")
                            if row_ind: self.cols_possibilities[ci] = self.remove_possibilities(self.cols_possibilities[ci], ri, val)   # remove the possibilities for the column depending on the value of the cell
                            else:       self.rows_possibilities[ri] = self.remove_possibilities(self.rows_possibilities[ri], ci, val)   # remove the possibilities for the row depending on the value of the cell

                            # ignore empty cells that should be empty
                            if not (self.board[ri][ci] == self.solution_grid[ri][ci] == -1):
                                """Update progress made by the bot"""
                                self.prev_progress = self.progress
                                self.progress = self.calculate_progress()
                            
                                """Update the last 3 interactions with the grid"""
                                if len(self.last_interactions) <= 3:
                                    #add most recent one at the beginning of the list
                                    self.last_interactions = [(ri, ci)] + self.last_interactions
                                else:
                                    #add most recent one at the beginning of the list
                                    self.last_interactions = [(ri, ci)] + self.last_interactions[:-1]
                            
                            # self.display_board_temporary()
                                
                        print("Progress progress: ", self.progress, " prev_progress: ", self.prev_progress)
                        """If progress stagnates or gets worse, get the recommended next steps and update the board with the recommended next step."""
                        if self.progress <= self.prev_progress:
                            print("Progress stagnated or got worse! progress: ", self.progress, " prev_progress: ", self.prev_progress)
                            self.ask_for_recommendation(row_ind, prob_respect_recommendation)
                                
                    self.update_done(row_ind, ind1)                 # update the rows_done or cols_done list when a row or column is completed
            self.check_with_solution() 
            print(f"self.solved: {self.solved}")
            if not self.solved:
                """Ask for the recommended next steps if the puzzle is not solved yet. Ask for next steps for specific row and column."""
                self.ask_for_recommendation(row_ind, prob_respect_recommendation)
   
    def add_nonunique_option(self, same_ind, row_ind):
        """
        Funciton adds/change a wrong cell to the list of cells that have only one possible solution for that cell.
        
        With a probability of 0.5:
            - Cell to be added is next to the last cell in the list. Usually to the right or below the last cell depending if row or column.
            - Invert the value of one random cell in the list.
            
        same_ind: list of tuples (index, value) in a row or column
        """
        upper_limit = self.no_of_cols if row_ind else self.no_of_rows       # upper limit of the row (width=number of columns) or column (height=number of rows)
        if len(same_ind) == 0: return same_ind
        
        prob = np.random.rand()
        if prob < 0.5:
            """ Add a mistake cell """
            if same_ind[-1][0] < upper_limit - 1:
                return same_ind + [(same_ind[-1][0] + 1, same_ind[-1][1])]      # add another cell to the right or below the last cell of the same value
            else:
                return same_ind[:-1] + [(same_ind[-1][0], -(same_ind[-1][1]) )] # make last cell wrong
        else:
            """ Change a cell to be wrong """
            random_idx = np.random.randint(0, len(same_ind)-1)
            return same_ind[:random_idx] + [(same_ind[random_idx][0], -(same_ind[random_idx][1]) )] + same_ind[random_idx+1:]
    
    def calculate_progress(self):
        """
        Calculate the progress by counting the number of cells that are correct in the progress grid and dividing to the total number of cells.
        """
        progress = 0
        no_cells_correct = 0   
        total_cells = self.no_of_cols * self.no_of_rows  
        # must ignore the initial cells and set all of them to -1 (empty) -> as it is done in the human UI
        self.progress_grid = [[-1 if cell == 0 else cell for cell in row] for row in self.board]
        for i in range(self.no_of_rows):
            for j in range(self.no_of_cols):
                if self.progress_grid[i][j] == self.solution_grid[i][j]:
                    no_cells_correct += 1
                    
        progress = no_cells_correct / total_cells
        return progress

    def ask_for_recommendation(self, row_ind, prob_respect_recommendation=1):
        """
        For a given row or column, ask for the recommended next steps if the progress stagnates or gets worse.
        Future work for the simulation benchmark:
        TODO: change to ask for whole-line recommendations with multiple next definite cells
        TODO: add the hint generation request to pipeline (can only do for directional hints as all info used in hints, conclusive hints might not return specific error location and general hints cannot be simulated with this algorithm)
        """
        # if a mistake was made, get the recommended next steps
        bot_helper = NonogramSolver(ROWS_VALUES=self.ROWS_VALUES,COLS_VALUES=self.COLS_VALUES, PROGRESS_GRID=self.board, SOLUTION_GRID=self.solution_grid, LAST_INTERACTIONS=self.last_interactions)
        next_recommended_steps, _, _ = bot_helper.recommend_next_action(no_next_steps=1)
        print(f"next_recommended_steps: {next_recommended_steps}")
        if next_recommended_steps == []: self.solved = True
        else:
            for step in next_recommended_steps:
                # if the recommendation is respected, update the board with the recommended next step
                if np.random.rand() < prob_respect_recommendation:
                    ri, ci, val = step
                    self.board[ri][ci] = val
                    if row_ind: self.cols_possibilities[ci] = self.remove_possibilities(self.cols_possibilities[ci], ri, val)
                    else:       self.rows_possibilities[ri] = self.remove_possibilities(self.rows_possibilities[ri], ci, val)
      
      
            
# if __name__ == '__main__':
#     # 0 = null cell, 1 = filled cell, -1 = empty cell
#     PROGRESS_GRID = [[0, 1, 1, 0, 0, 0, 0, 1, 1, 0], [1, 1, 0, 1, 1, 1, 1, 0, 1, 1], [1, 0, 1, 1, 1, 0, 1, 1, 0, 1], [0, 1, 1, 1, 1, 0, 1, 1, 1, 0], [0, 1, 1, 1, 1, 0, 1, 1, 1, 0], [0, 1, 1, 1, 0, 1, 1, 1, 1, 0], [0, 1, 1, 0, 1, 1, 1, 1, 1, 0], [0, 0, 1, 1, 1, 1, 1, 1, 0, 0], [0, 0, 0, 1, 1, 1, 1, 0, 0, 0], [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]]
#     PROGRESS_GRID =  [[-1 if cell == 0 else cell for cell in row] for row in PROGRESS_GRID]
#     ROWS_VALUES, COLS_VALUES = count_consecutive_cells(PROGRESS_GRID)
#     # ROWS_VALUES = [[2], [4], [6], [4, 3], [5, 4], [2, 3, 2], [3, 5], [5], [3], [2], [2], [6]]
#     # COLS_VALUES = [[3], [5], [3, 2, 1], [5, 1, 1], [12], [3, 7], [4, 1, 1, 1], [3, 1, 1], [4], [2]]
#     # PROGRESS_GRID = [[0 for c in range(len(COLS_VALUES))] for r in range(len(ROWS_VALUES))]
    
#     solver = NonogramSolver(ROWS_VALUES=ROWS_VALUES,COLS_VALUES=COLS_VALUES, PROGRESS_GRID=PROGRESS_GRID)#, savepath='data/nonogram_solver') # add a savepath to save the board at each iteration
#     solver.display_board()
    
#     # IDEA: instead of the grid starting from 0s, starts from a given grid state
#     # -> currently it can only add 1s, but it should be able to add 0s as well (it currently only solved the missing cell mistake, but i should add so it solved the filled cell mistake as well)