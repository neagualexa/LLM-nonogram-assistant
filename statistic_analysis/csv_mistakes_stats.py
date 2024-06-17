import os
import glob
import pandas as pd
import ast

def calculate_average_and_range_mistakes(mistakes_file):
    # Read mistakes data
    mistakes_data = pd.read_csv(mistakes_file)

    # Drop any rows with missing values
    mistakes_data.dropna(inplace=True)

    # Set 'Level' column as the index
    mistakes_data.set_index('Level', inplace=True)

    # Calculate the average mistakes per level
    average_mistakes = mistakes_data.mean(axis=1)

    # Calculate the range of mistakes per level
    range_mistakes = mistakes_data.std(axis=1)
    # range_mistakes = mistakes_data.max(axis=1) - mistakes_data.min(axis=1)

    return average_mistakes, range_mistakes

def reorder_data(df, custom_order):
    df['Level'] = pd.Categorical(df['Level'], categories=custom_order, ordered=True)
    df.sort_values('Level', inplace=True)
    # if level is not in custom_order, it will be removed from the DataFrame
    df = df.dropna(subset=['Level'])
    return df

def calculate_statistics_for_both(tailored_file, untailored_file, output_file, custom_order):
    # Calculate average and range mistakes for tailored data
    tailored_average, tailored_range = calculate_average_and_range_mistakes(tailored_file)
    
    # Calculate average and range mistakes for untailored data
    untailored_average, untailored_range = calculate_average_and_range_mistakes(untailored_file)
    
    # Align both series to a common set of levels
    common_levels = tailored_average.index.union(untailored_average.index)
    tailored_average = tailored_average.reindex(common_levels, fill_value=0)
    tailored_range = tailored_range.reindex(common_levels, fill_value=0)
    untailored_average = untailored_average.reindex(common_levels, fill_value=0)
    untailored_range = untailored_range.reindex(common_levels, fill_value=0)
    
    # Create a DataFrame to store the results
    statistics_df = pd.DataFrame({
        'Level': common_levels,
        'Tailored_Average': tailored_average.values,
        'Tailored_Range': tailored_range.values,
        'Untailored_Average': untailored_average.values,
        'Untailored_Range': untailored_range.values
    })
    
    # Reorder data based on custom order
    statistics_df = reorder_data(statistics_df, custom_order)
    
    # Save the DataFrame to a CSV file
    statistics_df.to_csv(output_file, index=False)

# usage
tailored_path = 'copy_data/tailored/'  
untailored_path = 'copy_data/untailored/'  
tailored_output_path = 'mistakes_tailored.csv'
untailored_output_path = 'mistakes_untailored.csv'
output_file = 'average_mistakes_statistics.csv'  # Adjust the output file path accordingly
custom_order = ['car', 'snail', 'mouse', 'rooster', 'invertedcar']
calculate_statistics_for_both(tailored_output_path, untailored_output_path, output_file, custom_order)


########################### STATS

# import pandas as pd
# from scipy.stats import ttest_ind, pearsonr

# # Read the data
# data = pd.read_csv(output_file)

# # Perform Pearson Correlation
# correlation, correlation_p_value = pearsonr(data['Tailored_Average'], data['Untailored_Average'])
# print(f"Pearson Correlation: R = {correlation} with p = {correlation_p_value}")
# Pearson Correlation: R = 0.8481197026381107 with p = 0.0694122162924949

# r(degress of freedom) = the r statistic, p = p value.
# 1. There are two ways to report p values. The first way is to cite the alpha value as in the second example above. The second way, very much the preferred way in the age of computer aided calculations (and the way recommended by the APA), is to report the exact p value (as in our main example). If you report the exact p value, then you need to state your alpha level early in your results section. The other thing to note here is that if your p value is less than .001, it's conventional simply to state p < .001, rather than give the exact value.
# 2. The r statistic should be stated at 2 decimal places.
# 3. Remember to drop the leading 0 from both r and the p value (i.e., not 0.34, but rather .34).
# 4. You don't need to provide the formula for r.
# 5. Degrees of freedom for r is N - 2 (the number of data points minus 2).


########################### Per level all participant mistakes ###########################
output_mistake_file = 'mistakes_statistics.csv'  # Adjust the output file path accordingly

tailored_mistakes = pd.read_csv(tailored_output_path)
untailored_mistakes = pd.read_csv(untailored_output_path)

for level in custom_order:
    level_tailored = tailored_mistakes[tailored_mistakes['Level'] == level]
    level_untailored = untailored_mistakes[untailored_mistakes['Level'] == level]
    combined_df = pd.DataFrame({
        'Level': level,
        'Mistake_tailored': level_tailored.values[0][1:],
        'Mistake_untailored': level_untailored.values[0][1:]
    })

    output_mistake_file = f'mistakes_{level}_statistics.csv'
    combined_df.to_csv(output_mistake_file, index=False)
    
# Perform t-test per level for all participants
for level in custom_order:
    output_mistake_file = f'mistakes_{level}_statistics.csv'
    data = pd.read_csv(output_mistake_file)
    tailored_data = data[data['Level'] == level]['Mistake_tailored']
    untailored_data = data[data['Level'] == level]['Mistake_untailored']
    t_stat, p_value = ttest_ind(tailored_data, untailored_data)
    print(f"Level: {level} - T-Statistic: {t_stat}, P-Value: {p_value}")
# Level: car - T-Statistic: -1.5796892811134748, P-Value: 0.13159012039440438
# Level: snail - T-Statistic: -1.4060329181047868, P-Value: 0.1767424516202018
# Level: mouse - T-Statistic: -1.5258816804201003, P-Value: 0.14441863484034384
# Level: rooster - T-Statistic: -1.1571834291382745, P-Value: 0.26232361398174736
# Level: invertedcar - T-Statistic: -0.9766656503108475, P-Value: 0.3416791229815451