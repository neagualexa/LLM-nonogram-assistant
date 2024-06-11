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
        levels = df['Level']    # Get all levels for the participant
        if participant_id not in hint_data:
            hint_data[participant_id] = {'car':pd.DataFrame(), 'invertedcar':pd.DataFrame()}
        for level in levels.unique():
            if level not in hint_data:
                hint_data[participant_id][level] = pd.DataFrame()
            hint_data[participant_id][level] = df[df['Level'] == level] #TODO: add filter to remove meaning hints
            print(participant_id, level, len(df[df['Level'] == level]))
    
    return hint_data

########################################### Class to handle the grid display and navigation
class NonogramVisualizer(tk.Frame):
    def __init__(self, parent, all_grids, participant_id, level, interaction_data, hint_data):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.all_grids = all_grids[participant_id].get(level, [])
        self.current_index = 0
        self.hint_index = 0
        self.participant_id = participant_id
        self.level = level
        
        self.hint = ''
        self.hint_updated = False
        
        self.interaction_data = interaction_data[participant_id][level]
        self.hint_data = hint_data[participant_id][level]
        
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.hint_text = tk.Text(self, wrap=tk.WORD, height=5, width=50)
        self.hint_text.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Next and back buttons
        self.back_button = Button(self, text="Back", command=self.previous_grid)
        self.back_button.pack(side=tk.LEFT, padx=10)
        
        self.next_button = Button(self, text="Next", command=self.next_grid)
        self.next_button.pack(side=tk.LEFT, padx=20)

        self.display_board()
        
        self.back_button = Button(self, text="Back to Levels", command=self.go_back_to_levels)
        self.back_button.pack(side=tk.BOTTOM)
        
        self.exit_button = Button(self, text="Exit", command=self.exit_application)
        self.exit_button.pack(side=tk.RIGHT, padx=10)
        
        self.bind("<Right>", self.next_grid)
        self.bind("<Left>", self.previous_grid)
        self.focus_set()

    def display_board(self):
        self.ax.clear()
        if self.all_grids:
            grid = self.all_grids[self.current_index]
            self.ax.imshow(grid, cmap='Greys', vmin=0, vmax=1)
            self.ax.set_title(f'Participant: {self.participant_id}, Level: {self.level}, Grid {self.current_index + 1}/{len(self.all_grids)}')
            # Add row and column indices
            for i in range(len(grid)):
                self.ax.text(-0.5, i, str(i + 1), va='center', ha='center', fontsize=8)
            for j in range(len(grid[0])):
                self.ax.text(j, -0.5, str(j + 1), va='center', ha='center', fontsize=8)
            
            # also show hint
            print(self.participant_id, self.level, self.hint_index, self.hint)
            self.hint_text.delete("1.0", tk.END)
            self.hint_text.insert(tk.END, self.hint)
            
            # Update next button color if hint is updated -> warning to evaluator that a hint was encountered
            if self.hint_updated:
                self.next_button.config(bg="red")
            else:
                self.next_button.config(bg="SystemButtonFace")
                
            self.hint_updated = False
        else:
            self.ax.set_title("No grids available for this level.")
        self.ax.axis('off')
        self.canvas.draw()

    def next_grid(self, event=None):
        if self.current_index < len(self.all_grids) - 1:
            self.current_index += 1
            self.display_board()
            hint = self.get_hint_after_interaction(self.interaction_data, self.hint_data, self.current_index, True)
            print("NEXT:", self.participant_id, self.level, self.hint_index, self.hint)

    def previous_grid(self, event=None):
        if self.current_index > 0:
            self.current_index -= 1
            self.display_board()
            # hint = self.get_hint_after_interaction(self.interaction_data, self.hint_data, self.current_index, False)
            # print("BACK:", self.participant_id, self.level, self.hint_index, hint)

    def go_back_to_levels(self):
        self.destroy()
        show_level_selection_screen(self.participant_id)
        
    def exit_application(self):
        self.parent.quit()
        
    def get_hint_after_interaction(self, interaction_data, hint_data, interaction_index, flag_forward=True):
    # keep track of current interaction index and hint index
    # for each interaction, check its timestamp and check if hint at index is after the interaction, if it is, display hint, else move to next hint
    # if no hint is found, display no hint
        interaction_timestamp = interaction_data.iloc[interaction_index]['Timestamp']
        hint = ''
        init_hint_index = hint_index = self.hint_index
        while hint_index < len(hint_data):
            hint_timestamp = hint_data.iloc[hint_index]['Timestamp']
            # print("interaction:", interaction_timestamp, "hint:", hint_timestamp, hint_data.iloc[hint_index]['Hint_Response'])
            if hint_timestamp <= interaction_timestamp:
                hint = hint_data.iloc[hint_index]['Hint_Response']
                if flag_forward:
                    self.hint_index += 1
                    self.hint_updated = True
                    self.hint = hint
                else:
                    if self.hint_index > init_hint_index:
                        self.hint_index -= 1
                break
            hint_index += 1
            
        return hint, hint_index

# Function to initialize the visualizer with the selected level
def initialize_visualizer(participant_id, level):
    for widget in root.winfo_children():
        widget.destroy()
    NonogramVisualizer(root, all_grids, participant_id, level, interaction_data, hint_data).pack(fill="both", expand=True)

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
    
    # Exit button
    exit_button = Button(level_selection_window, text="Exit", command=root.quit)
    exit_button.pack()

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
    
    # Exit button
    exit_button = Button(root, text="Exit", command=root.quit)
    exit_button.pack()

# Path to the folder containing the CSV files
folder_path = '../../Experiment/Participant_Data_CSV/copy_data/tailored/'

# Load all CSV files and extract grids
interaction_data = read_interaction_data(folder_path)
all_grids = load_grids_from_file(interaction_data)
print(f"Loaded {len(all_grids)} participants.")
print(all_grids.keys())
hint_data = read_hint_data(folder_path)

# Create the main window
root = tk.Tk()
root.title("Nonogram Visualizer")

# Show the participant selection screen
show_participant_selection_screen()

# Run the tkinter main loop
root.mainloop()
