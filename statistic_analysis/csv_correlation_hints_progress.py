# Pearson Correlation between number of hints used and progress acieved per level for each participant

from scipy.stats import pearsonr
import os
import glob
import pandas as pd
from scipy.stats import ttest_ind

# cannot use ['Nb_Hints_Used'] as it contains meaning hints which are not part of puzzle solving
def read_csv_files(folder_path, keyword):
    # Find all CSV files in the folder with the specified keyword in their name
    csv_files = glob.glob(os.path.join(folder_path, f'*{keyword}*.csv'))
    
    # Read all CSV files into a list of DataFrames
    data_frames = [pd.read_csv(file) for file in csv_files]
    
    # Concatenate all DataFrames into a single DataFrame
    combined_df = pd.concat(data_frames, ignore_index=True)
    
    return combined_df

def count_hints_non7(folder_path):
    # read the progress files in the folder_path
    progress = read_csv_files(folder_path, 'progress')
    # count number of hints that are not 7 per level
    hints = progress.groupby(['User', 'Level'])['Hint_Level'].apply(lambda x: (x != 7).sum())
    return hints

def group_data_by_level(df):
    hint_levels = {}
    custom_levels = ['snail', 'mouse', 'rooster']
    for level in custom_levels:
        if level not in hint_levels:
            hint_levels[level] = df[df['Level'] == level]
        else:
            hint_levels[level] += df[df['Level'] == level]
            
    return hint_levels

def read_level_data(folder_path, keyword):
    level_data = {}
    csv_files = glob.glob(os.path.join(folder_path, f'*level*{keyword}*.csv'))
    custom_order = ['car', 'snail', 'mouse', 'rooster', 'invertedcar'] # no 'heart'
    
    for file in csv_files:
        level = file.split('_')[2]
        df = pd.read_csv(file)
        level_data[level] = df
    
    return level_data

# def correlation_per_level(tailored_data, untailored_data):
#     for level in tailored_data:
#         if level in untailored_data:
#             print(f"Calculating correlation for level {level}")
#             tailored_hints = tailored_data[level]['Nb_Hints_Used']
#             tailored_progress = tailored_data[level]['Progress']
#             untailored_hints = untailored_data[level]['Nb_Hints_Used']
#             untailored_progress = untailored_data[level]['Progress']
            
#             print(f"{level} Tailored data: {list(tailored_hints)} {list(tailored_progress)}")
#             print(f"{level} Untailored data: {list(untailored_hints)} {list(untailored_progress)}")
            
#             # correlation, correlation_p_value = calculate_correlation(tailored_hints, tailored_progress)
#             # print(f"{level} TAILORED: Pearson Correlation: R = {correlation} with p = {correlation_p_value}")
#             # correlation_u, correlation_p_value_u = calculate_correlation(untailored_hints, untailored_progress)
#             # print(f"{level} UNTAILORED: Pearson Correlation: R = {correlation_u} with p = {correlation_p_value_u}")
#         else:
#             print(f"Untailored data for level {level} not found")

def calculate_correlation(hints, progress):
    # Perform Pearson Correlation
    correlation, correlation_p_value = pearsonr(hints, progress)
    return correlation, correlation_p_value

def run_correlation_tests(tailored_hints, untailored_hints, tailored_data, untailored_data):
    for level in tailored_hints:
        if level in untailored_hints:
            print(f"Running correlation test for level {level}")
            tailored_hints_level = tailored_hints[level]
            tailored_progress_level = tailored_data[level]['Progress']
            untailored_hints_level = untailored_hints[level]
            untailored_progress_level = untailored_data[level]['Progress']
            
            # print(f"{level} Tailored data: {list(tailored_hints_level)} {list(tailored_progress_level)}")
            # print(f"{level} Untailored data: {list(untailored_hints_level)} {list(untailored_progress_level)}")
            
            correlation, correlation_p_value = calculate_correlation(tailored_hints_level, tailored_progress_level)
            print(f"{level} TAILORED: Pearson Correlation: R = {correlation} with p = {correlation_p_value}")
            correlation_u, correlation_p_value_u = calculate_correlation(untailored_hints_level, untailored_progress_level)
            print(f"{level} UNTAILORED: Pearson Correlation: R = {correlation_u} with p = {correlation_p_value_u}")
        else:
            print(f"Untailored data for level {level} not found")
    
 
def main(folder):
    hint_count = count_hints_non7(folder)

    level_hints = {
        'snail': {},
        'mouse': {},
        'rooster': {}
    }
    hints_list = {}

    for participant, level in hint_count.index:
        if level in level_hints:
            if participant not in level_hints[level]:
                level_hints[level][participant] = hint_count[participant, level]
            else:
                level_hints[level] += hint_count[participant, level]

    for level, hints in level_hints.items():
        print(f"Level: {level}, Hints: {hints}")
        # convert hints into a list
        hints_list[level] = list(hints.values())
    
    return hints_list       

# usage
tailored_folder = './copy_data/tailored/'
untailored_folder = './copy_data/untailored/'
folder = './'

tailored_data = read_level_data(folder, '_tailored')
untailored_data = read_level_data(folder, '_untailored')
# correlation_per_level(tailored_data, untailored_data)

tailored_hints = main(tailored_folder)
untailored_hints = main(untailored_folder)

run_correlation_tests(tailored_hints, untailored_hints, tailored_data, untailored_data)