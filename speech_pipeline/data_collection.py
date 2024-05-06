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
    
    fieldnames_audio = ['id', 'Hint_Id', 'Hint_Level', 'Hint', 'Audio_Generation_Latency', 'Audio_Playback_Latency', 'Timestamp']
    csv_handler_audio = CSVHandler('data/data_audio.csv', fieldnames_audio)
    csv_handler_audio.initialize_file()
    
    return csv_handler_audio


# CSV Database Initialization
csv_handler_audio = initialize_csv_database()    
