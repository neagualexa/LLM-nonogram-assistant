import os
import glob
import pandas as pd
from scipy.stats import ttest_ind

def read_level_data(folder_path, keyword):
    level_data = {}
    csv_files = glob.glob(os.path.join(folder_path, f'*level*{keyword}*.csv'))
    custom_order = ['car', 'snail', 'mouse', 'rooster', 'invertedcar'] # no 'heart'
    
    for file in csv_files:
        level = file.split('_')[2]
        df = pd.read_csv(file)
        # level_data[level] = df['puzzle_duration'] # uncomment to get durations
        # level_data[level] = df['Progress']  # uncomment to get progress
        level_data[level] = df['Nb_Hints_Used']  # uncomment to get Nb_Hints_Used
    
    return level_data

def run_t_tests(tailored_data, untailored_data):
    t_test_results = {}
    for level in tailored_data:
        if level in untailored_data:
            print(f"Running t-test for level {level}")
            # print(f"Tailored data: {tailored_data[level]}")
            # print(f"Untailored data: {untailored_data[level]}")
            t_stat, p_value = ttest_ind(tailored_data[level], untailored_data[level])
            t_test_results[level] = (t_stat, p_value)
        else:
            t_test_results[level] = ("Untailored data for this level not found", None)
    return t_test_results

def get_average_range_durations(tailored_data, untailored_data):
    average_durations = {}
    range_durations = {}
    for level in tailored_data:
        if level in untailored_data:
            print(f"Calculating average durations for level {level}")
            tailored_avg = tailored_data[level].mean()
            untailored_avg = untailored_data[level].mean()
            average_durations[level] = (tailored_avg, untailored_avg)
            
            level_tailored_data = pd.Series(tailored_data[level])
            level_untailored_data = pd.Series(untailored_data[level])
            range_durations[level] = (level_tailored_data.std(), level_untailored_data.std())
            # range_durations[level] = (tailored_data[level].max() - tailored_data[level].min(), untailored_data[level].max() - untailored_data[level].min())
        else:
            average_durations[level] = ("Untailored data for this level not found", None)
    return average_durations, range_durations

def main(tailored_folder, untailored_folder, output_file):
    tailored_data = read_level_data(tailored_folder, '_tailored')
    untailored_data = read_level_data(untailored_folder, '_untailored')
    
    t_test_results = run_t_tests(tailored_data, untailored_data)
    average_durations, range_durations = get_average_range_durations(tailored_data, untailored_data)
    # print(average_durations, range_durations)
    with open("t_test_"+output_file, 'w') as f:
        f.write("Level,T-Statistic,P-Value\n")
        for level, results in t_test_results.items():
            if isinstance(results, tuple):
                f.write(f"{level},{results[0]},{results[1]}\n")
            else:
                f.write(f"{level},{results}\n")
                
    with open(output_file, 'w') as f:
        f.write("Level,Tailored_Average_Duration,Tailored_Range,Untailored_Average_Duration,Untailored_Range\n") # spaces matter, DO NOT put spaces after commas
        for level, durations in average_durations.items():
            f.write(f"{level},{durations[0]},{range_durations[level][0]},{durations[1]},{range_durations[level][1]}\n")

# Example usage
tailored_folder = './'  # Replace with the path to your tailored data folder
untailored_folder = './'  # Replace with the path to your untailored data folder
# output_file = 'average_duration_statistics.csv'
# output_file = 'average_progress_statistics.csv'
output_file = 'average_hints_statistics.csv'

main(tailored_folder, untailored_folder, output_file)

########################### STATS

import pandas as pd
from scipy.stats import ttest_ind

# Read the data
data = pd.read_csv(output_file)

# Perform independent t-test
t_stat, p_value = ttest_ind(data['Tailored_Average_Duration'], data['Untailored_Average_Duration'])

print(f"Duration T-Test:\nT-statistic: {t_stat}, P-value: {p_value}")
# T-statistic: -1.0826382210943484, P-value: 0.31051854759943226 # without heart tutorial level