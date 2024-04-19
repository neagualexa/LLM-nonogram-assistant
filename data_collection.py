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
        with open(self.filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writerow(entry)

    def update_entry(self, entry_id, new_values):
        entries = self.read_entries()
        for entry in entries:
            if entry['id'] == str(entry_id):
                entry.update(new_values)
                break
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
    
def initialize_csv_database():
    fieldnames_progress = ['id', 'User', 'Level', 'Position', 'Hint_Response', 'Observation_Response', 'Positioning_Response', 'Position_Description', 'Overall_Latency', 'Hint_Latency', 'Observation_Latency', 'Position_Latency', 'Hint_Model', 'Observation_Model', 'Position_Model',  'Mistakes_per_Hint_Wrong', 'Mistakes_per_Hint_Missing', 'Timestamp']
    csv_handler_progress = CSVHandler('data/data_progress.csv', fieldnames_progress)
    csv_handler_progress.initialize_file()
    
    fieldnames_meaning = ['id', 'User', 'Level', 'Meaning', 'Guess', 'Approved', 'Model', 'Latency', 'Timestamp']
    csv_handler_meaning = CSVHandler('data/data_meaning.csv', fieldnames_meaning)
    csv_handler_meaning.initialize_file()
    
    fieldnames_game = ['id', 'User', 'Level', 'Completed', 'onTime', 'Duration', 'Meaning_Completed', 'Nb_Hints_Used', 'Timestamp']
    csv_handler_game = CSVHandler('data/data_game.csv', fieldnames_game)
    csv_handler_game.initialize_file()
    
    return csv_handler_progress, csv_handler_meaning, csv_handler_game


# CSV Database Initialization
csv_handler_progress, csv_handler_meaning, csv_handler_game = initialize_csv_database()    
    
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