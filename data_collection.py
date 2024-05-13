#### OLD: using CSV module ####

import csv
import os
class CSVHandler:
    def __init__(self, filename, fieldnames):
        self.filename = filename
        self.fieldnames = fieldnames
        self.file_exists = os.path.isfile(filename)

    def initialize_file(self):
        if not self.file_exists:
            with open(self.filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writeheader()
            self.file_exists = True

    def add_entry(self, entry):
        # Ensure that the entry has only expected fieldnames
        self._validate_fieldnames(entry)
        
        with open(self.filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writerow(entry)

    def update_entry(self, entry_id, new_values):
        entries = self.read_entries()
        # Ensure the keys in new_values are a subset of fieldnames
        self._validate_fieldnames(new_values)
        
        # Update the matching entry
        updated = False
        for entry in entries:
            if entry['id'] == str(entry_id):
                entry.update(new_values)
                updated = True
                break
        
        if not updated:
            raise KeyError(f"Entry with id {entry_id} not found")
        
        # Write the updated entries back to the CSV
        with open(self.filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(entries)

    def read_entries(self):
        entries = []
        with open(self.filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                entries.append(row)
        return entries
    
    def read_entries_specific_level(self, level):
        entries = []
        with open(self.filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Level'] == level:
                    entries.append(row)
        return entries
    
    def get_length(self):
        with open(self.filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            return len(list(reader))
        
    def _validate_fieldnames(self, data):
        # Ensure the keys are a subset of expected fieldnames
        if not set(data.keys()).issubset(set(self.fieldnames)):
            raise ValueError("Data contains fields not in expected fieldnames")

# Initializes the CSV database files
def initialize_csv_database():
    # old approach fieldnames
    # fieldnames_progress = ['id', 'Hint_Level', 'User', 'Level', 'Position', 'Hint_Response', 'Observation_Response', 'Positioning_Response', 'Position_Description', 'Overall_Latency', 'Hint_Latency', 'Observation_Latency', 'Position_Latency', 'Hint_Model', 'Observation_Model', 'Position_Model',  'Mistakes_per_Hint_Wrong', 'Mistakes_per_Hint_Missing', 'Timestamp']
    fieldnames_progress = ['id', 'User', 'Level', 'Hint_Level', 'Hint_Response', 'Next_Steps', 'Descriptive_Next_steps', 'Overall_Latency', 'Hint_Latency', 'Hint_Model', 'Progress', 'Previous_Progress', 'Hint_Session_Counter', 'Timestamp']
    csv_handler_progress = CSVHandler('data/data_progress.csv', fieldnames_progress)
    csv_handler_progress.initialize_file()
    
    fieldnames_meaning = ['id', 'User', 'Level', 'Meaning', 'Guess', 'Approved', 'Model', 'Latency', 'Timestamp']
    csv_handler_meaning = CSVHandler('data/data_meaning.csv', fieldnames_meaning)
    csv_handler_meaning.initialize_file()
    
    fieldnames_game = ['id', 'User', 'Level', 'Completed', 'onTime', 'Duration', 'Meaning_Completed', 'Nb_Hints_Used', 'Timestamp']
    csv_handler_game = CSVHandler('data/data_game.csv', fieldnames_game)
    csv_handler_game.initialize_file()
    
    # each Cell_i is a list of  (Row, Column, Row Group Size, Column Group Size)
    fieldnames_interaction = ['id', 'User', 'Level', 'Cell_1', 'Cell_2', 'Cell_3', 'Grid', 'Progress_Grid', 'Target_row', 'Target_col', 'Predicted_row', 'Predicted_col']
    csv_handler_interaction = CSVHandler('data/data_interaction.csv', fieldnames_interaction)
    csv_handler_interaction.initialize_file()
    
    fieldnames_audio = ['id', 'Hint_Id', 'Hint_Level', 'Hint', 'Audio_Generation_Latency', 'Audio_Playback_Latency', 'Timestamp']
    csv_handler_audio = CSVHandler('data/data_audio.csv', fieldnames_audio)
    csv_handler_audio.initialize_file()
    
    return csv_handler_progress, csv_handler_meaning, csv_handler_game, csv_handler_interaction, csv_handler_audio


# CSV Database Initialization
csv_handler_progress, csv_handler_meaning, csv_handler_game, csv_handler_interaction, csv_handler_audio = initialize_csv_database()    
    
# Examples to use the CSVHandler class
# # Add an entry in MEANING DATA
# count_entries = len(csv_handler_meaning.read_entries())
# new_entry = {'id': count_entries, 'User': 'test', 'Level': 'test', 'Meaning': 'test', 'Guess': 'test', 'Approved': 'test', 'Model': 'test', 'Latency': 'test', 'Timestamp': 'test'}
# csv_handler_meaning.add_entry(new_entry)

# # Update an entry in MEANING DATA
# updated_values = {'User': 'NEW test'}
# csv_handler_meaning.update_entry(count_entries, updated_values)

# # Read all entries
# entries = csv_handler_meaning.read_entries()
# print(entries)
