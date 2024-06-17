import os
import glob
import pandas as pd
import ast

def read_interaction_data(folder_path):
    interaction_data = {}
    csv_files = glob.glob(os.path.join(folder_path, '*interaction*.csv'))
    
    for file in csv_files:
        df = pd.read_csv(file)
        df.dropna(inplace=True)  # Drop rows with NaN values
        participant_id = os.path.basename(file).split('_')[0]  # Assuming the file name is the participant id
        interaction_data[participant_id] = df
    
    return interaction_data

def count_mistakes(df):
    mistakes_per_level = {}
    
    for _, row in df.iterrows():
        if row['Grid'] == "" or row['Progress_Grid'] == "" or row['Cell_1'] == "" or row['Level'] == "":
            continue
        level = row['Level']
        grid = ast.literal_eval(row['Grid'])
        progress_grid = ast.literal_eval(row['Progress_Grid'])
        cell_1 = ast.literal_eval(row['Cell_1']) if row['Cell_1'] else None

        mistakes = 0

        if cell_1:
            row_idx, col_idx = cell_1
            # Adjust indices if necessary (e.g., if 1-based indexing)
            row_idx -= 1
            col_idx -= 1
            # Check if the cell that was last interacted with is a mistake
            if grid[row_idx][col_idx] != progress_grid[row_idx][col_idx]:
                mistakes += 1

        participant_id = row['User']
        if level not in mistakes_per_level:
            mistakes_per_level[level] = {}
        if participant_id not in mistakes_per_level[level]:
            mistakes_per_level[level][participant_id] = 0
        mistakes_per_level[level][participant_id] += mistakes
    
    return mistakes_per_level

def reorder_data(df, custom_order):
    df['Level'] = pd.Categorical(df['Level'], categories=custom_order, ordered=True)
    df.sort_values('Level', inplace=True)
    return df

def main_with_ids(interaction_folder, custom_order, output_file):
    interaction_data = read_interaction_data(interaction_folder)
    all_mistakes = {}
    
    for participant_id, df in interaction_data.items():
        reordered_data = reorder_data(df, custom_order)
        mistakes_per_participant = count_mistakes(reordered_data)
        
        for level, participant_mistakes in mistakes_per_participant.items():
            ### {'aa68': 2},{'az23': 32}
            if level not in all_mistakes:
                all_mistakes[level] = {}
            if participant_id not in all_mistakes[level]:
                all_mistakes[level][participant_id] = participant_mistakes
    
    with open(output_file, 'w') as f:
        participant_ids = list(interaction_data.keys())
        f.write("Level," + ",".join(f"{participant_id}_mistakes" for participant_id in participant_ids) + "\n")
        for level, participant_mistakes in all_mistakes.items():
            mistakes_str = ",".join(str(participant_mistakes.get(participant_id, 0)) for participant_id in participant_ids)
            f.write(f"{level},{mistakes_str}\n")

def main(interaction_folder, custom_order, output_file):
    interaction_data = read_interaction_data(interaction_folder)
    all_mistakes = {}
    
    for participant_id, df in interaction_data.items():
        reordered_data = reorder_data(df, custom_order)
        mistakes_per_participant = count_mistakes(reordered_data)
        
        for level, participant_mistakes in mistakes_per_participant.items():
            if level not in all_mistakes:
                all_mistakes[level] = {}
            all_mistakes[level][participant_id] = participant_mistakes.get(participant_id, 0)
    
    with open(output_file, 'w') as f:
        f.write("Level," + ",".join(interaction_data.keys()) + "\n")
        for level, participant_mistakes in all_mistakes.items():
            mistakes_str = ",".join(str(participant_mistakes.get(participant_id)) for participant_id in interaction_data.keys())
            f.write(f"{level},{mistakes_str}\n")
            
def main_extra(interaction_folder, custom_order, output_file):
    interaction_data = read_interaction_data(interaction_folder)
    all_extra_clicks = {}
    
    for participant_id, df in interaction_data.items():
        reordered_data = reorder_data(df, custom_order)
        # len(participant entries per level) - 60 = extra clicks
        # for level in custom_order:
        #     clicks = len(reordered_data[reordered_data['Level'] == level])
        #     print(f"{participant_id} - {level}: {clicks}, {clicks - 60} extra clicks")
        extra_clicks_per_participant = {level: len(reordered_data[reordered_data['Level'] == level]) - 60 for level in custom_order}
        
        for level, participant_clicks in extra_clicks_per_participant.items():
            if level not in all_extra_clicks:
                all_extra_clicks[level] = {}
            all_extra_clicks[level][participant_id] = participant_clicks
    
    with open(output_file, 'w') as f:
        f.write("Level," + ",".join(interaction_data.keys()) + "\n")
        for level, participant_mistakes in all_extra_clicks.items():
            mistakes_str = ",".join(str(participant_mistakes.get(participant_id)) for participant_id in interaction_data.keys())
            f.write(f"{level},{mistakes_str}\n")


# usage
tailored_path = 'copy_data/tailored/'  
untailored_path = 'copy_data/untailored/'  
tailored_output_path = 'mistakes_tailored.csv'
untailored_output_path = 'mistakes_untailored.csv'
tailored_extra_clicks_path = 'extra_clicks_tailored.csv'
untailored_extra_clicks_path = 'extra_clicks_untailored.csv'

custom_order = ['car', 'snail', 'mouse', 'rooster', 'invertedcar'] # no 'heart'
# main(tailored_path, custom_order, tailored_output_path)
# main(untailored_path, custom_order, untailored_output_path)

main_extra(tailored_path, custom_order, tailored_extra_clicks_path)
main_extra(untailored_path, custom_order, untailored_extra_clicks_path)