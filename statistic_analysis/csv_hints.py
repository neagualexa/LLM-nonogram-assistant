import os
import glob
import pandas as pd
import ast

def read_hint_data(folder_path):
    data = {}
    csv_files = glob.glob(os.path.join(folder_path, '*progress*.csv'))

    for file in csv_files:
        df = pd.read_csv(file)
        # df.dropna(inplace=True)  # Drop rows with NaN values
        participant_id = os.path.basename(file).split('_')[0]  # Assuming the file name is the participant id
        data[participant_id] = df
    
    return data

# over all participants, count the number of hints used per level in game
def count_hint_per_level(df):
    hints = {}
    for participant_id, df in df.items():
        for index, row in df.iterrows():
            level = row['Level']
            hints_used = row['Hint_Level']
            if level in hints:
                hints[level] += hints_used
            else:
                hints[level] = hints_used
    return hints

def count_hint_style_per_level(df):
    hints = {}
    for participant_id, df in df.items():
        for index, row in df.iterrows():
            level = row['Level']
            hints_used = row['Hint_Level']
            if level in hints:
                hints[level].append(hints_used)
            else:
                hints[level] = [hints_used]
    
    # count number of hints used per level 
    count_hints = {} 
    for level in hints:
        if level not in count_hints:
            count_hints[level] = {}
        for hint in hints[level]:
            if hint in count_hints[level]:
                count_hints[level][hint] += 1
            else:
                count_hints[level][hint] = 1
    
    return count_hints

# get number of hints per style on average that are used per level
# each participant has a list of hints used per level
# for each level, get the average number of hints used per style
def get_avg_hint_style_per_level(df):
    hints = {}
    for participant_id, df in df.items():
        for index, row in df.iterrows():
            level = row['Level']
            hints_used = row['Hint_Level']
            if level in hints:
                hints[level].append(hints_used)
            else:
                hints[level] = [hints_used]
    
    # count number of hints used per level 
    count_hints = {} 
    for level in hints:
        if level not in count_hints:
            count_hints[level] = {}
        for hint in hints[level]:
            if hint in count_hints[level]:
                count_hints[level][hint] += 1
            else:
                count_hints[level][hint] = 1
    
    # get average number of hints used per style per level
    avg_hints = {}
    for level in count_hints:
        if level not in avg_hints:
            avg_hints[level] = {}
        for hint in count_hints[level]:
            avg_hints[level][hint] = count_hints[level][hint] / len(hints[level])
    
    return avg_hints

def split_data_by_level(data, output_folder):
    level_data = {}
    
    for participant_id, df in data.items():
        for _, row in df.iterrows():
            level = row['Level']
            if level not in level_data:
                level_data[level] = []
            level_data[level].append(row)
    
    # Convert list of rows to DataFrame for each level and save to CSV
    for level, rows in level_data.items():
        level_df = pd.DataFrame(rows)
        output_path = os.path.join(output_folder, f'level_{level}.csv')
        level_df.to_csv(output_path, index=False)
        print(f'Saved {level} data to {output_path}')
    
    return level_data

paths = 'copy_data/tailored/'

# count_per_hint_level = count_hint_style_per_level(read_hint_data(paths))
# print("Tailored data hint levels count: ", count_per_hint_level)
# avg = get_avg_hint_style_per_level(read_hint_data(paths))
# print("Tailored data hint levels average: ", avg)
split_data_by_level(read_hint_data(paths),'./hints_per_level')

# paths = 'copy_data/untailored/'
# count_per_hint_level = count_hint_style_per_level(read_hint_data(paths))
# print("Untailored data hint levels count: ", count_per_hint_level)
# avg = get_avg_hint_style_per_level(read_hint_data(paths))
# print("Untailored data hint levels average: ", avg)