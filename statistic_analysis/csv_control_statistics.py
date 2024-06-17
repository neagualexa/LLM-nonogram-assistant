import pandas as pd
from scipy.stats import ttest_ind, pearsonr

########################### Per level all participant PROGRESS ###########################
custom_order = ['car', 'snail', 'mouse', 'rooster', 'invertedcar']

for level in custom_order:
    tailored_output_path = f'output_level_{level}_tailored.csv'
    untailored_output_path = f'output_level_{level}_untailored.csv'
    
    tailored_mistakes = pd.read_csv(tailored_output_path)
    untailored_mistakes = pd.read_csv(untailored_output_path)
    
    # Perform t-test per level for all participants
    t_stat, p_value = ttest_ind(tailored_mistakes['puzzle_duration'], untailored_mistakes['puzzle_duration'])
    print(f"Level: {level} - T-Statistic: {t_stat}, P-Value: {p_value}")
    

    