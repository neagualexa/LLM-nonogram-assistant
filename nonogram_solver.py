# Nonogram solver/validator solution adapted from Hennie de Harder's article "Solving Nonograms with 120 Lines of Code" 
# (https://towardsdatascience.com/solving-nonograms-with-120-lines-of-code-a7c6e0f627e4) [published: Jul 1, 2022]
# Credits of original code to: Hennie de Harder
# NOTES:
# For nonograms with only one solution
# 0 = initial cell, 1 = filled cell, -1 = empty cell
# 0 indexed grid and constraints

import os, time
from itertools import combinations
import numpy as np 
import matplotlib.pyplot as plt 
from IPython.display import clear_output
from grid_difference_checker import count_consecutive_cells

class NonogramSolver:
    def __init__(self, ROWS_VALUES, COLS_VALUES, PROGRESS_GRID, savepath=''):
        self.ROWS_VALUES = ROWS_VALUES
        self.no_of_rows = len(ROWS_VALUES)
        # self.rows_changed = [0] * self.no_of_rows
        self.rows_done = [0] * self.no_of_rows

        self.COLS_VALUES = COLS_VALUES
        self.no_of_cols = len(COLS_VALUES)
        # self.cols_changed = [0] * self.no_of_cols
        self.cols_done = [0] * self.no_of_cols

        self.solved = False 
        self.shape = (self.no_of_rows, self.no_of_cols)
        self.board = [[0 for c in range(self.no_of_cols)] for r in range(self.no_of_rows)]
        self.progress_grid = PROGRESS_GRID
        self.savepath = savepath
        if self.savepath != '': self.n = 0

        # step 1: Defining all possible solutions for every row and col
        self.rows_possibilities = self.create_possibilities(ROWS_VALUES, self.no_of_cols)
        self.cols_possibilities = self.create_possibilities(COLS_VALUES, self.no_of_rows)
        
        while not self.solved:
            # step 2: Order indici by lowest 
            self.lowest_rows = self.select_index_not_done(self.rows_possibilities, 1)
            self.lowest_cols = self.select_index_not_done(self.cols_possibilities, 0)
            self.lowest = sorted(self.lowest_rows + self.lowest_cols, key=lambda element: element[1])

            # step 3: Get only zeroes or only ones of lowest possibility 
            for ind1, _, row_ind in self.lowest:
                if not self.check_done(row_ind, ind1):
                    if row_ind: values = self.rows_possibilities[ind1]
                    else: values = self.cols_possibilities[ind1]
                    same_ind = self.get_only_one_option(values)
                    for ind2, val in same_ind:
                        if row_ind: ri, ci = ind1, ind2
                        else: ri, ci = ind2, ind1 
                        if self.board[ri][ci] == 0:
                            # only update if the cell is gray (initial cell) or empty
                            print(f'NEXT STEP to fill: row: {ri}, col: {ci}, val: {val}')
                            self.board[ri][ci] = val
                            if row_ind: self.cols_possibilities[ci] = self.remove_possibilities(self.cols_possibilities[ci], ri, val)
                            else: self.rows_possibilities[ri] = self.remove_possibilities(self.rows_possibilities[ri], ci, val)
                            clear_output(wait=True)
                            self.display_board_temporary()
                            if self.savepath != '':
                                self.save_board()
                                self.n += 1
                        else:
                            print('Cell already filled')
                    self.update_done(row_ind, ind1)
            self.check_solved()
                    
    def create_possibilities(self, values, no_of_other):
        possibilities = []
        
        for v in values:
            groups = len(v)
            no_empty = no_of_other-sum(v)-groups+1
            ones = [[1]*x for x in v]
            res = self._create_possibilities(no_empty, groups, ones)
            possibilities.append(res)  
        
        return possibilities

    def _create_possibilities(self, n_empty, groups, ones):
        res_opts = []
        for p in combinations(range(groups+n_empty), groups):
            selected = [-1]*(groups+n_empty)
            ones_idx = 0
            for val in p:
                selected[val] = ones_idx
                ones_idx += 1
            res_opt = [ones[val]+[-1] if val > -1 else [-1] for val in selected]
            res_opt = [item for sublist in res_opt for item in sublist][:-1]
            res_opts.append(res_opt)
        return res_opts

    def select_index_not_done(self, possibilities, row_ind):
        s = [len(i) for i in possibilities]
        if row_ind:
            return [(i, n, row_ind) for i, n in enumerate(s) if self.rows_done[i] == 0]
        else:
            return [(i, n, row_ind) for i, n in enumerate(s) if self.cols_done[i] == 0]

    def get_only_one_option(self, values):
        return [(n, np.unique(i)[0]) for n, i in enumerate(np.array(values).T) if len(np.unique(i)) == 1]

    def remove_possibilities(self, possibilities, i, val):
        return [p for p in possibilities if p[i] == val]

    def display_board_temporary(self):
        plt.imshow(self.board, cmap='Greys')
        plt.axis('off')
        # close the plot to continue
        plt.show(block=False)
        plt.pause(1)
        plt.close()
        
    def display_board(self):
        plt.imshow(self.board, cmap='Greys')
        plt.axis('off')
        plt.show()

    def save_board(self, increase_size=20):
        name = f'0000000{str(self.n)}'[-8:]
        increased_board = np.zeros(np.array((self.no_of_rows, self.no_of_cols)) * increase_size)
        for j in range(self.no_of_rows):
            for k in range(self.no_of_cols):
                increased_board[j * increase_size : (j+1) * increase_size, k * increase_size : (k+1) * increase_size] = self.board[j][k]
        plt.imsave(os.path.join(self.savepath, f'{name}.jpeg'), increased_board, cmap='Greys', dpi=1000)

    def update_done(self, row_ind, idx):
        if row_ind: vals = self.board[idx]
        else: vals = [row[idx] for row in self.board]
        if 0 not in vals:
            if row_ind: self.rows_done[idx] = 1
            else: self.cols_done[idx] = 1 

    def check_done(self, row_ind, idx):
        if row_ind: return self.rows_done[idx]
        else: return self.cols_done[idx]

    def check_solved(self):
        if 0 not in self.rows_done and 0 not in self.cols_done:
            self.solved = True
      
      
            
if __name__ == '__main__':
    # 0 = initial cell, 1 = filled cell, -1 = empty cell
    PROGRESS_GRID = [[0, 1, 1, 0, 0, 0, 0, 1, 1, 0], [1, 1, 0, 1, 1, 1, 1, 0, 1, 1], [1, 0, 1, 1, 1, 0, 1, 1, 0, 1], [0, 1, 1, 1, 1, 0, 1, 1, 1, 0], [0, 1, 1, 1, 1, 0, 1, 1, 1, 0], [0, 1, 1, 1, 0, 1, 1, 1, 1, 0], [0, 1, 1, 0, 1, 1, 1, 1, 1, 0], [0, 0, 1, 1, 1, 1, 1, 1, 0, 0], [0, 0, 0, 1, 1, 1, 1, 0, 0, 0], [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]]
    PROGRESS_GRID =  [[-1 if cell == 0 else cell for cell in row] for row in PROGRESS_GRID]
    ROWS_VALUES, COLS_VALUES = count_consecutive_cells(PROGRESS_GRID)
    # ROWS_VALUES = [[2], [4], [6], [4, 3], [5, 4], [2, 3, 2], [3, 5], [5], [3], [2], [2], [6]]
    # COLS_VALUES = [[3], [5], [3, 2, 1], [5, 1, 1], [12], [3, 7], [4, 1, 1, 1], [3, 1, 1], [4], [2]]
    # PROGRESS_GRID = [[0 for c in range(len(COLS_VALUES))] for r in range(len(ROWS_VALUES))]
    
    solver = NonogramSolver(ROWS_VALUES=ROWS_VALUES,COLS_VALUES=COLS_VALUES, PROGRESS_GRID=PROGRESS_GRID)#, savepath='data/nonogram_solver') # add a savepath to save the board at each iteration
    solver.display_board()
    
    # IDEA: instead of the grid starting from 0s, starts from a given grid state
    # -> currently it can only add 1s, but it should be able to add 0s as well (it currently only solved the missing cell mistake, but i should add so it solved the filled cell mistake as well)