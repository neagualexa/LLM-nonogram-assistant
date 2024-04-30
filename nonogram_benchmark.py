from nonogram_solver import NonogramSolver
from progress_tracking import recommend_next_steps

def run_benchmark(row_clues, column_clues, solutionGrid):
    """
    Run a bot that will aim to solve a nonogram puzzle optimally by respecting the algoritmn. 
        However, with some probability, the bot will make a mistake (fill in a wrong cell).
            Simulating a Human misinterpreting the clues of the puzzle.
    When such a derailing event occurs, a hint will be generated (with next best steps) in order to help the bot to recover and continue solving the puzzle.
        However, with some probability, the bot will ignore the hint and continue solving the puzzle on its own.
            Simulating a Human not understanding the hint provided and moving forward on their own without implementing the next best steps.
    """
    
    # start from empty progress grid
    initialGrid = [[0 for _ in range(len(column_clues))] for _ in range(len(row_clues))]
    last_interactions = []
    bot_solver = NonogramSolver(ROWS_VALUES=row_clues,COLS_VALUES=column_clues, PROGRESS_GRID=initialGrid, SOLUTION_GRID=solutionGrid, LAST_INTERACTIONS=last_interactions)
    bot_solver.solve()                  # solve the puzzle optimally to find the solution and set the self.solutionGrid
    # reset the NonogramSolver progress
    bot_solver.board = [[0 for _ in range(len(column_clues))] for _ in range(len(row_clues))]  # reset the board to empty
    bot_solver.solved = False
    bot_solver.rows_done = [0] * bot_solver.no_of_rows  # reset the rows_done list
    bot_solver.cols_done = [0] * bot_solver.no_of_rows  # reset the cols_done list
    
    bot_solver.solve_with_mistakes()    # solve the puzzle with mistakes to find the solution and set the self.board
    bot_solver.display_board()
    
    return

if __name__ == "__main__":
    temp_row_clues = [[2], [4], [6], [4, 3], [5, 4], [2, 3, 2], [3, 5], [5], [3], [2], [2], [6]]            # length = 12
    temp_column_clues = [[3], [5], [3, 2, 1], [5, 1, 1], [12], [3, 7], [4, 1, 1, 1], [3, 1, 1], [4], [2]]   # length = 10
    temp_solutionGrid = [[0 for _ in range(len(temp_column_clues))] for _ in range(len(temp_row_clues))]
    print("Benchmarking the Nonogram Solver...")
    print("Height(nb rows): ", len(temp_row_clues), " Width(nb cols): ", len(temp_column_clues))
    run_benchmark(temp_row_clues, temp_column_clues, temp_solutionGrid)