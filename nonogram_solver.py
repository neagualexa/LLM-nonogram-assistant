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
        
        self.savepath = savepath
        if self.savepath != '': self.n = 0

    def solve(self):
        """
        Method that solves the nonogram puzzle.
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
                    self.update_done(row_ind, ind1)                 # update the rows_done or cols_done list when a row or column is completed
            self.check_solved()                                     # check if the puzzle is solved
    
    
    def recommend_next_action(self, no_next_steps = 1):
        """
        Method that recommends the next cell to fill in the nonogram puzzle based on the current grid progress state.
        The method also considers the last interactions with the grid to prioritize the rows and columns that were last interacted with. (including the rows and columns right next to the last interacted row or column)
        Always look in the vicinity of the last interaction.
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

            # step 5.1.2: Get the priority rows and columns based on the last interactions with the grid (also consider the rows and columns right next to the last interacted row or column)
            self.priority_lines = self.get_priority_lines(self.last_interactions)
            self.process_explained.append("- user interacted last with: " + str(self.last_interactions) + "\n")
            # Step 5.1.3: Then re-sort the combined list (of rows and columns) by priority of interaction
            self.priority_lowest = sorted(self.lowest, key=self.custom_sort_priority)

            # step 5.2: Get only zeroes or only ones of lowest possibility (rows or cols with least possibilities of combinations of completions)
            for ind1, _, row_ind in self.priority_lowest:
                if not self.check_done(row_ind, ind1):
                    self.process_explained.append("-- \talgo pass through the rows or cols with least possibilities of combinations of completions & are not done yet")
                    self.process_explained.append(f"-- \tcurrent {'row' if row_ind else 'column'} {ind1}.")
                    # If the row or column is not done yet, get the possibilities for the row or column
                    if row_ind: values = self.rows_possibilities[ind1]
                    else:       values = self.cols_possibilities[ind1]
                    # Then identifiy which cells in a set of possiblities of row/column patterns have a consistent value across all possibilities, and return those cells.
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
                                print(f'Recommended next cell is: row: {ri}, col: {ci}, val: {val} [0 indexed]')
                                if no_next_steps > 0:
                                    next_recommended_steps.append((ri, ci, val))
                                    no_next_steps -= 1
                                
                                if no_next_steps == 0:
                                    return next_recommended_steps
                                
                            self.board[ri][ci] = val
                            # If loop not broken, then a cell was completed in that row/column, so remove the other possibilities that do not match that specific cell's state at its supposed location
                            if row_ind: self.cols_possibilities[ci] = self.remove_possibilities(self.cols_possibilities[ci], ri, val)
                            else:       self.rows_possibilities[ri] = self.remove_possibilities(self.rows_possibilities[ri], ci, val)
                            self.process_explained.append(f"--- \tRemove the possibilities that do not match the value of the cell at the given location (row: {ri}, col: {ci}, val: {val})(remove impossible solutions for other rows or columns).")
                    # A new row/column has been fully completed, so mark them as done
                    self.update_done(row_ind, ind1)
                    self.process_explained.append(f"-- \tUpdate that {'row' if row_ind else 'column' } {ind1} is completed with all cells.\n")
            # check if nonogram grid is completed
            self.check_solved()
            self.process_explained.append(f"\n-- \tCheck if the nonogram puzzle is solved. {self.solved}")
        return next_recommended_steps # No recommended next step as the grid is solved
    
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
        """
        priority_lines = {
            "rows": [],
            "cols": []
        }
        
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
        
        (i, n, row_ind): tuple of integers (index, number of possibilities, row or column index boolean)
        """
        i, n, row_ind = item
        priority = 1  # Default priority (1 means not in the top list)
        
        # Assign priority if it's in the priority list; 0 means it is in the top list (no priority between the top list elements)
        if row_ind and i in self.priority_lines["rows"]:
            priority = 0
        elif not row_ind and i in self.priority_lines["cols"]:
            priority = 0
        
        return (priority, n)

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