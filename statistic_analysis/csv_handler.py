import os
import glob
import pandas as pd
import numpy as np

def read_csv_files(folder_path, keyword):
    # Find all CSV files in the folder with the specified keyword in their name
    csv_files = glob.glob(os.path.join(folder_path, f'*{keyword}*.csv'))
    
    # Read all CSV files into a list of DataFrames
    data_frames = [pd.read_csv(file) for file in csv_files]
    
    # Concatenate all DataFrames into a single DataFrame
    combined_df = pd.concat(data_frames, ignore_index=True)
    
    return combined_df
    
def get_last_entries(df, group_by_columns):
    # Sort by Timestamp and keep the last entry for each user and level
    df = df.sort_values(by='Timestamp').drop_duplicates(subset=group_by_columns, keep='last')
    return df

def get_first_entries(df, group_by_columns):
    # Sort by Timestamp and keep the first entry for each user and level
    df = df.sort_values(by='Timestamp').drop_duplicates(subset=group_by_columns, keep='first')
    return df

#################################################################
def reshape_durations(folder_path):
    # Read the data
    game_df = read_csv_files(folder_path, 'game')
    interaction_df = read_csv_files(folder_path, 'interaction')
    meaning_df = read_csv_files(folder_path, 'meaning')
    
    # Get the last entry per user per level for interaction and meaning data
    interaction_last = get_last_entries(interaction_df, ['User', 'Level'])
    interaction_first = get_first_entries(interaction_df, ['User', 'Level'])
    meaning_last = get_last_entries(meaning_df, ['User', 'Level'])
    interaction_merged = pd.merge(interaction_last, interaction_first, on=['User', 'Level'], suffixes=('_interaction_last', '_interaction_first'))
    
    # Merge interaction and meaning data on User and Level
    merged_df = pd.merge(interaction_merged, meaning_last, on=['User', 'Level'], how='left')
    # print("merged_df fieldnames: ", merged_df.columns)

    # Calculate meaning_duration
    merged_df['Timestamp_meaning'] = pd.to_datetime(merged_df['Timestamp'])
    merged_df['Timestamp_interaction_last'] = pd.to_datetime(merged_df['Timestamp_interaction_last'])    
    merged_df['Timestamp_interaction_first'] = pd.to_datetime(merged_df['Timestamp_interaction_first'])
    merged_df['meaning_duration'] = (merged_df['Timestamp_meaning'] - merged_df['Timestamp_interaction_last']).dt.total_seconds() # seconds
    merged_df['puzzle_duration'] = (merged_df['Timestamp_interaction_last'] - merged_df['Timestamp_interaction_first']).dt.total_seconds() # seconds
    
    # Merge the meaning_duration into the game data
    game_df = pd.merge(game_df, merged_df[['User', 'Level', 'Timestamp_meaning', 'Timestamp_interaction_last', 'Timestamp_interaction_first', 'meaning_duration', 'puzzle_duration']], on=['User', 'Level'], how='left')
    # print("game_df fieldnames: ", game_df.columns)
    
    # Fill missing values in meaning_duration with Duration - Timestamp_interaction_last
    game_df['meaning_duration'] = game_df['meaning_duration'].fillna(game_df['Duration'] - game_df['puzzle_duration'])
    game_df['puzzle_duration'] = game_df['Duration'] - game_df['meaning_duration']
    
    # If Completed == false then puzzle_duration = Duration
    # TODO: add or game_df['Progress'] != 1.0) cause could be that the complete flag has not updated but the progress is 1.0 (to check idk)
    game_df['puzzle_duration'] = np.where(game_df['Completed'] == False, game_df['Duration'], game_df['puzzle_duration'])
    game_df['meaning_duration'] = np.where(game_df['Completed'] == False, 
                                            np.where(game_df['Meaning_Completed'] == False, 
                                                    game_df['Duration'] - game_df['puzzle_duration'],
                                                    game_df['meaning_duration']), game_df['meaning_duration'])
    # if game_df['Completed'] == False and game_df['Meaning_Completed'] == False:
    #     game_df['meaning_duration'] = game_df['Duration'] - game_df['puzzle_duration']
    
    return game_df
    
def separate_data_into_levels(game_df):
    # Create a list of DataFrames, where each DataFrame contains data for a single level
    custom_order = ['car', 'snail', 'mouse', 'rooster', 'invertedcar'] # no 'heart'
    
    game_df = game_df[game_df['Level'].isin(custom_order)]
    game_df.loc[:, 'Level'] = pd.Categorical(game_df['Level'], categories=custom_order, ordered=True)
    
    # split the data into levels based on custom_order
    level_dfs = [game_df[game_df['Level'] == level] for level in custom_order]    
    # print("level_dfs: ", level_dfs)
    return level_dfs

def group_control_tests(game_df):
    control_tests = ['car', 'invertedcar']
    control_df = game_df[game_df['Level'].isin(control_tests)]
    return control_df
#################################################################
tailored_path = 'copy_data/tailored/'  
untailored_path = 'copy_data/untailored/'  
tailored_output_path = 'output_tailored.csv'
untailored_output_path = 'output_untailored.csv'

tailored = [True, False]

for tailored in tailored:
    if tailored:
        game_df = reshape_durations(tailored_path)
        game_df.to_csv(tailored_output_path, index=False)
        
        levels_dfs = separate_data_into_levels(game_df)
        for i, level_df in enumerate(levels_dfs):
            level = level_df['Level'].iloc[0]
            level_df.to_csv(f'output_level_{level}_tailored.csv', index=False)

        control_df = group_control_tests(game_df)
        control_df.to_csv('output_control_tailored.csv', index=False)
    else:
        game_df = reshape_durations(untailored_path)
        game_df.to_csv(untailored_output_path, index=False)
        
        level_df = separate_data_into_levels(game_df)
        for i, level_df in enumerate(level_df):
            level = level_df['Level'].iloc[0]
            level_df.to_csv(f'output_level_{level}_untailored.csv', index=False)
        
        control_df = group_control_tests(game_df)
        control_df.to_csv('output_control_untailored.csv', index=False)


