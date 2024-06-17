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

def get_first_5_interactions(df):
    # df.sort_values('Timestamp', inplace=True)
    return df.head(5)

def check_majority_direction(df, level):
    # each interaction is a Cell_1 which shows the last row, column interacted with
    # we can calculate the majority direction by checking the first 5 interactions and if the row or column is the same
    
    # get the first 5 interactions
    first_5 = get_first_5_interactions(df)
    
    if len(first_5) == 0:
        return 'no interactions'
    # get the row and column of the first interaction
    first_interaction = first_5.iloc[0]
    first_row, first_col = ast.literal_eval(first_interaction['Cell_1'])
    
    # check if the majority direction is row or column
    row_majority = 0
    col_majority = 0
    for _, interaction in first_5.iterrows():
        row, col = ast.literal_eval(interaction['Cell_1'])
        if row == first_row:
            row_majority += 1
        if col == first_col:
            col_majority += 1
            
    if row_majority > col_majority:
        return 'row'
    else:
        return 'column'
    
def reorder_data(df, custom_order):
    df['Level'] = pd.Categorical(df['Level'], categories=custom_order, ordered=True)
    df.sort_values('Level', inplace=True)
    return df

def main(interaction_folder, output_file):
    interaction_data = read_interaction_data(interaction_folder)
    majority_directions = {}
    custom_order = ['heart', 'snail', 'mouse'] # only levels with an equal good start with either row or columns
    
    for participant_id, df in interaction_data.items():
        reordered_data = reorder_data(df, custom_order)
        for level in custom_order:
            if level not in majority_directions:
                majority_directions[level] = {}
            majority_directions[level][participant_id] = check_majority_direction(reordered_data[reordered_data['Level'] == level], level)
            print(f"Participant: {participant_id}, Level: {level}, Majority Direction: {majority_directions[level][participant_id]}")
    # get percentage of row and column majority for all data
    row_majority = 0
    col_majority = 0
    for level, participants in majority_directions.items():
        
        for participant, direction in participants.items():
            if direction == 'row':
                row_majority += 1
            else:
                col_majority += 1
    participants = len(majority_directions['heart'])
    levels = len(majority_directions)
    print(f"For all levels, Row Majority: {row_majority/(participants*levels):.2%}, Column Majority: {col_majority/(participants*levels):.2%}")
   
    
           
    # with open(output_file, 'w') as f:
    #     f.write("Level,Participant_ID,Majority_Direction\n")
    #     for level, participants in majority_directions.items():
    #         for participant, direction in participants.items():
    #             f.write(f"{level},{participant},{direction}\n")
            
# usage
all_path = 'copy_data/*/'  
output_file = 'majority_directions.csv'

main(all_path, output_file)
# Mainly looking at column first
# Level: heart, Row Majority: 30.00%, Column Majority: 70.00%
# Level: snail, Row Majority: 20.00%, Column Majority: 80.00%
# Level: mouse, Row Majority: 45.00%, Column Majority: 55.00%

# For all levels, Row Majority: 35.00%, Column Majority: 65.00%
