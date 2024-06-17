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

def read_audio_data(folder_path):
    data = {}
    csv_files = glob.glob(os.path.join(folder_path, '*audio*.csv'))
    
    for file in csv_files:
        df = pd.read_csv(file)
        df.dropna(inplace=True)  # Drop rows with NaN values
        participant_id = os.path.basename(file).split('_')[0]  # Assuming the file name is the participant id
        data[participant_id] = df
    
    return data

################# overall whole data regardless of hint level #################
def get_avg_latency(df, keyword):
    overall_latencies = []
    # each entry has a 'keyword' field, merge all participant latencies into one list
    for participant_id, df in df.items():
        # print(participant_id, "df fieldnames: ", df.keys())
        
        try:
            overall_latency = df[keyword]
            overall_latencies = overall_latency.dropna()
            overall_latency = overall_latency.tolist()
            overall_latencies += overall_latency
            # print(participant_id, "overall_latency: ", overall_latencies)
        except:
            print("No such field: ", keyword)
            continue
        
    average_latency = sum(overall_latencies) / len(overall_latencies)
    deviation_latency = overall_latencies.std()
        
    return average_latency,deviation_latency

def get_knowledge_latency(df):
    overall_latencies = []
    hint_latencies = []
    # each entry has a 'keyword' field, merge all participant latencies into one list
    for participant_id, df in df.items():
        # print(participant_id, "df fieldnames: ", df.keys())
        
        try:
            overall_latency = df['Overall_Latency']
            overall_latencies = overall_latency.dropna()
            overall_latency = overall_latency.tolist()
            overall_latencies += overall_latency
            # print(participant_id, "overall_latency: ", overall_latencies)
        except:
            print("No such field: ", "Overall_Latency")
            continue
        
        try:
            hint_latency = df['Hint_Latency']
            hint_latencies = hint_latency.dropna()
            hint_latency = hint_latency.tolist()
            hint_latencies += hint_latency
            # print(participant_id, "hint_latency: ", hint_latency)
        except:
            print("No such field: ", "Hint_Latency")
            continue
    
    # difference preserve pandas series
    overall_latencies = overall_latencies - hint_latencies
    average_latency = sum(overall_latencies) / len(overall_latencies)
    deviation_latency = overall_latencies.std()
        
    return average_latency,deviation_latency

################# per hint level #################
# same task of getting average latency, but for each Hint_Level in the df
def get_avg_latency_per_level(df, keyword):
    overall_latencies = {}
    overall = {}
    deviation = {}
    for participant_id, df in df.items():
        for hint_level in df['Hint_Level'].unique():
            overall_latency = df[df['Hint_Level'] == hint_level][keyword]
            overall_latencies[hint_level] = overall_latency.dropna().tolist()
            
    for hint_level, latencies in overall_latencies.items():
        average_latency = sum(latencies) / len(latencies)
        overall[hint_level] = average_latency
        # convert to pandas series to use std() method
        l = pd.Series(latencies)
        deviation[hint_level] = l.std()
            
    return overall, deviation

def get_knowledge_latency_per_level(df):
    overall_latencies = {}
    hint_latencies = {}
    overall = {}
    deviation = {}
    for participant_id, df in df.items():
        for hint_level in df['Hint_Level'].unique():
            overall_latency = df[df['Hint_Level'] == hint_level]['Overall_Latency']
            overall_latencies[hint_level] = overall_latency.dropna().tolist()
            hint_latency = df[df['Hint_Level'] == hint_level]['Hint_Latency']
            hint_latencies[hint_level] = hint_latency.dropna().tolist()
    
    for hint_level, latencies in overall_latencies.items():
        overall_latency = pd.Series(latencies)
        hint_latency = pd.Series(hint_latencies[hint_level])
        overall_latencies[hint_level] = overall_latency - hint_latency
        average_latency = sum(overall_latencies[hint_level]) / len(overall_latencies[hint_level])
        overall[hint_level] = average_latency
        deviation[hint_level] = overall_latencies[hint_level].std()
            
    return overall, deviation

def count_hint_levels(df):
    hint_levels = {}
    for participant_id, df in df.items():
        # print(participant_id, "df fieldnames: ", df['Hint_Level'].unique())
        for hint_level in df['Hint_Level']:
            if hint_level not in hint_levels:
                hint_levels[hint_level] = 1
            else:
                hint_levels[hint_level] += 1
    return hint_levels
# knoweldge base generation: overall_latency - hint_latency in progress file
# hint generation API: hint_latency
# audio generation latency: audio_latency
# sum of all latencies: overall_latency

paths = 'copy_data/*/'

# average_latency_hint, deviation_latency_hint = get_avg_latency(read_hint_data(paths), 'Hint_Latency')
# print("Average Hint Generation Latency: ", average_latency_hint, " ms +/- ", deviation_latency_hint)

# average_latency_audio, deviation_latency_audio = get_avg_latency(read_audio_data(paths), 'Audio_Generation_Latency')
# print("Average Audio Latency: ", average_latency_audio, " ms +/- ", deviation_latency_audio)

# average_latency, deviation_latency = get_avg_latency(read_hint_data(paths), 'Overall_Latency')
# print("Average Hint OVERALL Latency: ", average_latency, " ms +/- ", deviation_latency)

# average_latency_knowledge, deviation_latency_knowledge = get_knowledge_latency(read_hint_data(paths))
# print("Server knowledge nase latency: ", average_latency_knowledge, " ms +/- ", deviation_latency_knowledge)


# Average Hint Generation Latency:  4.088490062444445  ms +/-  0.8351638259007498
# Average Audio Latency:  2.705576349894206  ms +/-  0.5893770024283179
# Average Hint OVERALL Latency:  4.1850953631111105  ms +/-  0.8746238415133698
# Server knowledge nase latency:  0.09660530066666666  ms +/-  0.06870456190422232

average_latency_hint_per_level, deviation_latency_hint_per_level = get_avg_latency_per_level(read_hint_data(paths), 'Hint_Latency')
print("Average Hint Generation Latency per level: ", average_latency_hint_per_level, " ms +/- ", deviation_latency_hint_per_level)

average_latency_audio_per_level, deviation_latency_audio_per_level = get_avg_latency_per_level(read_audio_data(paths), 'Audio_Generation_Latency')
print("Average Audio Latency per level: ", average_latency_audio_per_level, " ms +/- ", deviation_latency_audio_per_level)

average_latency_per_level, deviation_latency_per_level = get_avg_latency_per_level(read_hint_data(paths), 'Overall_Latency')
print("Average Hint OVERALL Latency per level: ", average_latency_per_level, " ms +/- ", deviation_latency_per_level)

average_latency_knowledge_per_level, deviation_latency_knowledge_per_level = get_knowledge_latency_per_level(read_hint_data(paths))
print("Server knowledge nase latency per level: ", average_latency_knowledge_per_level, " ms +/- ", deviation_latency_knowledge_per_level)

game_latency = pd.Series(average_latency_per_level.values()).mean()
game_deviation = pd.Series(deviation_latency_per_level.values()).mean()
count_overall = count_hint_levels(read_hint_data(paths))
print("Game latency: ", game_latency, " ms +/- ", game_deviation, " with ", count_overall, " entries")
# SIMPLIFIED FOR REPORT
# Average Hint Generation Latency per level:    {0: 2.60, 7: 1.88, 1: 2.98, 2: 2.25}  ms +/-  {0: 0.917, 7: 0.337, 1: 0.518, 2: 0.465}
# Average Audio Latency per level:              {0: 1.12, 7: 1.29, 1: 1.48, 2: 1.24}  ms +/-  {0: 0.047, 7: 0.166, 1: 0.419, 2: 0.137}
# Average Hint OVERALL Latency per level:       {0: 2.63, 7: 1.91, 1: 3.27, 2: 2.32}  ms +/-  {0: 0.923, 7: 0.335, 1: 0.608, 2: 0.490}
# Server knowledge nase latency per level:      {0: 0.03, 7: 0.03, 1: 0.29, 2: 0.07}  ms +/-  {0: 0.005, 7: 0.004, 1: 0.300, 2: 0.045}
# Game latency:                                 2.53  ms +/-  0.589

# whole output:
# Average Hint Generation Latency per level:    {0: 2.5988784631093345, 7: 1.8831161022, 1: 2.9828048545, 2: 2.2456561925000003}  ms +/-  {0: 0.9176619158636508, 7: 0.33716949530065976, 1: 0.5175259023233653, 2: 0.4648245818058161}
# Average Audio Latency per level:              {0: 1.1247688770294186, 7: 1.2914772415161133, 1: 1.4803118228912349, 2: 1.238141369819641}  ms +/-  {0: 0.046650676831247816, 7: 0.16632038440081962, 1: 0.41941960187596494, 2: 0.1373803576540284}
# Average Hint OVERALL Latency per level:       {0: 2.631396293640137, 7: 1.9144289492, 1: 3.272231976333334, 2: 2.3151960970000003}  ms +/-  {0: 0.9229558815022515, 7: 0.3358866141823531, 1: 0.6079661613208255, 2: 0.49048743655681637}
# Server knowledge nase latency per level:      {0: 0.03251783053080256, 7: 0.03131284699999996, 1: 0.2894271218333333, 2: 0.06953990450000003}  ms +/-  {0: 0.0052959012022915095, 7: 0.004447987027827459, 1: 0.3003934361497724, 2: 0.04514474629388678}
# Game latency:  2.533313329043368  ms +/-  0.5893240233905616  with  {0: 31, 7: 37, 1: 143, 2: 128}  entries