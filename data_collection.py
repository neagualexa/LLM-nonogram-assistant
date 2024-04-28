
# Class to handle CSV operations with pandas
import pandas as pd

# CSV file handling class with key error handling
class CSVHandler:
    def __init__(self, filename, fieldnames):
        self.filename = filename
        self.fieldnames = fieldnames

    def initialize_file(self):
        df = pd.DataFrame(columns=self.fieldnames)
        df.to_csv(self.filename, index=False)

    def add_entry(self, entry):
        df = pd.read_csv(self.filename)
        # Check if the 'id' key exists to avoid KeyError
        if 'id' in entry:
            # Ensure the column names align with the fieldnames
            df = pd.concat([df, pd.DataFrame([entry], columns=self.fieldnames)], ignore_index=True)
            df.to_csv(self.filename, index=False)
        else:
            print("Error: 'id' key not found in entry")

    def update_entry(self, entry_id, new_values):
        df = pd.read_csv(self.filename)
        try:
            # Ensure the 'id' key exists before trying to update
            df.loc[df['id'] == str(entry_id), list(new_values.keys())] = list(new_values.values())
            df.to_csv(self.filename, index=False)
        except KeyError:
            # Handle the error, potentially logging it or taking another action
            print(f"KeyError: 'id' key not found in DataFrame")

    def read_entries(self):
        try:
            df = pd.read_csv(self.filename)
            return df.to_dict(orient='records')
        except KeyError as e:
            print(f"KeyError: {e}")
            return []
        
    def get_length(self):
        df = pd.read_csv(self.filename)
        return len(df)


# Initializes the CSV database files
def initialize_csv_database():
    fieldnames_progress = ['id', 'Hint_Level', 'User', 'Level', 'Position', 'Hint_Response', 'Observation_Response', 'Positioning_Response', 'Position_Description', 'Overall_Latency', 'Hint_Latency', 'Observation_Latency', 'Position_Latency', 'Hint_Model', 'Observation_Model', 'Position_Model',  'Mistakes_per_Hint_Wrong', 'Mistakes_per_Hint_Missing', 'Timestamp']
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
    
    return csv_handler_progress, csv_handler_meaning, csv_handler_game, csv_handler_interaction


# CSV Database Initialization
csv_handler_progress, csv_handler_meaning, csv_handler_game, csv_handler_interaction = initialize_csv_database()    
    
# # Examples to use the CSVHandler class
#     # # Add an entry in MEANING DATA
#     # count_entries = len(csv_handler_meaning.read_entries())
#     # new_entry = {'id': count_entries, 'User': 'test', 'Level': 'test', 'Meaning': 'test', 'Guess': 'test', 'Approved': 'test', 'Model': 'test', 'Latency': 'test', 'Timestamp': 'test'}
#     # csv_handler_meaning.add_entry(new_entry)
    
#     # # Update an entry in MEANING DATA
#     # updated_values = {'User': 'NEW test'}
#     # csv_handler_meaning.update_entry(count_entries, updated_values)

#     # # Read all entries
#     # entries = csv_handler_meaning.read_entries()
#     # print(entries)


#### OLD: using CSV module ####

# import csv
# import os

# class CSVHandler:
#     def __init__(self, filename, fieldnames):
#         self.filename = filename
#         self.fieldnames = fieldnames
#         self.file_exists = os.path.isfile(filename)

#     def initialize_file(self):
#         if not self.file_exists:
#             with open(self.filename, 'w', newline='') as csvfile:
#                 writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
#                 writer.writeheader()
#             self.file_exists = True

#     def add_entry(self, entry):
#         with open(self.filename, 'a', newline='') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
#             writer.writerow(entry)

#     def update_entry(self, entry_id, new_values):
#         entries = self.read_entries()
#         for entry in entries:
#             if entry['id'] == str(entry_id):
#                 entry.update(new_values)
#                 break
#         with open(self.filename, 'w', newline='') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
#             writer.writeheader()
#             writer.writerows(entries)

#     def read_entries(self):
#         entries = []
#         with open(self.filename, 'r', newline='') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 entries.append(row)
#         return entries