import pandas as pd
import ast
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import glob
import os
import tkinter as tk
from tkinter import Listbox, Button, SINGLE, END, Toplevel

# Function to load grids from a dictionary of dataframes
def load_grids_from_file(data):
    grids = {}
    for participant_id, levels in data.items():
        grids[participant_id] = {}
        # print(participant_id, levels.keys())
        for level, df in levels.items():
            # print(level, df.keys())
            participant_grids = df['Progress_Grid'].apply(ast.literal_eval).tolist()
            grids[participant_id][level] = participant_grids
    return grids

# Function to read interaction data from CSV files in a folder
def read_interaction_data(folder_path):
    interaction_data = {}
    csv_files = glob.glob(os.path.join(folder_path, '*interaction*.csv'))
    
    for file in csv_files:
        df = pd.read_csv(file)
        df.dropna(inplace=True)  # Drop rows with NaN values
        participant_id = os.path.basename(file).split('_')[0]  # Extract participant ID from filename
        levels = df['Level']    # Get all levels for the participant
        if participant_id not in interaction_data:
            interaction_data[participant_id] = {}
        for level in levels.unique():
            if level not in interaction_data[participant_id]:
                interaction_data[participant_id][level] = pd.DataFrame()
            interaction_data[participant_id][level] = df[df['Level'] == level]
            print(participant_id, level, len(df[df['Level'] == level]))   

    return interaction_data

def read_hint_data(folder_path):
    hint_data = {}
    csv_files = glob.glob(os.path.join(folder_path, '*progress*.csv'))
    
    for file in csv_files:
        df = pd.read_csv(file)
        df.dropna(inplace=True)  # Drop rows with NaN values
        participant_id = os.path.basename(file).split('_')[0]  # Extract participant ID from filename
        hint_data[participant_id] = df
    
    return hint_data

# Class to handle the grid display and navigation
class NonogramVisualizer(tk.Frame):
    def __init__(self, parent, all_grids, participant_id, level):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.all_grids = all_grids[participant_id].get(level, [])
        self.current_index = 0
        self.participant_id = participant_id
        self.level = level
        
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.display_board()
        
        self.back_button = Button(self, text="Back to Levels", command=self.go_back_to_levels)
        self.back_button.pack(side=tk.BOTTOM)
        
        self.bind("<Right>", self.next_grid)
        self.bind("<Left>", self.previous_grid)
        self.focus_set()

    def display_board(self):
        self.ax.clear()
        if self.all_grids:
            grid = self.all_grids[self.current_index]
            self.ax.imshow(grid, cmap='Greys', vmin=0, vmax=1)
            self.ax.set_title(f'Participant: {self.participant_id}, Level: {self.level}, Grid {self.current_index + 1}/{len(self.all_grids)}')
        else:
            self.ax.set_title("No grids available for this level.")
        self.ax.axis('off')
        self.canvas.draw()

    def next_grid(self, event=None):
        if self.current_index < len(self.all_grids) - 1:
            self.current_index += 1
            self.display_board()

    def previous_grid(self, event=None):
        if self.current_index > 0:
            self.current_index -= 1
            self.display_board()

    def go_back_to_levels(self):
        self.destroy()
        show_level_selection_screen(self.participant_id)

# Function to initialize the visualizer with the selected level
def initialize_visualizer(participant_id, level):
    for widget in root.winfo_children():
        widget.destroy()
    NonogramVisualizer(root, all_grids, participant_id, level).pack(fill="both", expand=True)

# Function to show the level selection screen
def show_level_selection_screen(participant_id):
    level_selection_window = Toplevel(root)
    level_selection_window.title("Select Level")
    
    listbox = Listbox(level_selection_window, selectmode=SINGLE)
    listbox.pack(fill="both", expand=True)

    # Add levels to the listbox
    for level in all_grids[participant_id]:
        listbox.insert(END, level)

    # Button to confirm level selection
    select_button = Button(level_selection_window, text="Select", command=lambda: initialize_visualizer(participant_id, listbox.get(listbox.curselection())))
    select_button.pack()

    # Button to go back to participant selection
    back_button = Button(level_selection_window, text="Back to Participants", command=show_participant_selection_screen)
    back_button.pack()

# Function to initialize the level selection screen
def initialize_level_selection(participant_id):
    show_level_selection_screen(participant_id)

# Function to show the participant selection screen
def show_participant_selection_screen():
    for widget in root.winfo_children():
        widget.destroy()
    
    listbox = Listbox(root, selectmode=SINGLE)
    listbox.pack(fill="both", expand=True)

    # Add participants to the listbox
    for participant_id in all_grids.keys():
        listbox.insert(END, participant_id)

    # Button to confirm participant selection
    select_button = Button(root, text="Select", command=lambda: initialize_level_selection(listbox.get(listbox.curselection())))
    select_button.pack()

# Path to the folder containing the CSV files
folder_path = '../../Experiment/Participant_Data_CSV/copy_data/tailored/'

# Load all CSV files and extract grids
data = read_interaction_data(folder_path)
all_grids = load_grids_from_file(data)
print(f"Loaded {len(all_grids)} participants.")
print(all_grids.keys())

# Create the main window
root = tk.Tk()
root.title("Nonogram Visualizer")

# Show the participant selection screen
show_participant_selection_screen()

# Run the tkinter main loop
root.mainloop()
