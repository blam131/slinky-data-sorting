import pandas as pd
import numpy as np
from coding_dict_master import coding_dict

MAX_DURATION = 1800
FLUENCY = 6

data = pd.read_csv("slinky_data.csv",
                    skiprows=1)

def search_cols():
    # Loops through each column head in csv to match question in dict
    for column_head in data.columns:
        for question in coding_dict:
            if question in column_head:
                check_and_replace(column_head, question)
               
def check_and_replace(col_head, question): 
    # Loops through question answers to change in dict and matches with column values
    for key, new_value in coding_dict[question].items():
        try:
            data.loc[data[col_head] == float(key), col_head] = new_value
        except (KeyError, ValueError):
            pass  

def filter_duration():
    # Filters out participants that took too long to answer the questions
    values_to_drop = data.loc[data["Duration (in seconds)"] > MAX_DURATION].index
    data.drop(index=values_to_drop, axis=0, inplace=True)

def filter_duplicate():
    # Checks for dupe IP addresses and deletes all but the first occurence 
    data.drop_duplicates(subset=["IP Address"], keep="first", inplace=True)

def filter_fluency():
    # Filters out participants that self reported a lower fluency score than required or chose not to disclose
    question = [head for head in data.columns if "fluency" in head]
    values_to_drop = data.loc[(data[question[0]] < FLUENCY) | (data[question[0]] == 8.0)].index
    data.drop(index=values_to_drop, axis=0, inplace=True)

def filter_incomplete_surveys():
    # Filters out incomplete surveys (often researcher previewing)
    values_to_drop = data.loc[data["Progress"] < 100].index
    data.drop(index=values_to_drop, axis=0, inplace=True)

def filter_experimenter_data():
    # Filters out experimenter data by searching for responses without an assigned condition
    # Also filters out data where participants did not consent 
    try:
        data.drop(data[data["DistributionChannel"].isin("preview", "test")], inplace=True)
    except KeyError:
        pass

    try:
        data.dropna(subset=["Condition_Identity_Intent_Art"], axis=0, inplace=True, how="all")
    except KeyError:
        pass

    try:
        data.dropna(subset=["Condition_Identity_Intent_Artifact"], axis=0, inplace=True, how="all")
    except KeyError:
        pass

    try:
        data.dropna(subset=["Condition_Quality"], axis=0, inplace=True, how="all")
    except KeyError:
        pass

def search_comprehension_cols():
    # Loops through each column head to search for comprehension questions
    # Grabs the column index and the row index of the first non-null value; row index used to find condition
    quote = "on the left?"
    for column_head in data.columns:
        if quote in column_head:
            col_loc = data.columns.get_loc(column_head)
            
            # Grabs condition name under the condition header on csv
            if "artist" in column_head:
                domain = "Condition_Identity_Intent_Art"
            elif "company" in column_head:
                domain = "Condition_Identity_Intent_Artifact"
            
            if data[column_head].first_valid_index() != None:
                condition = data.loc[data[column_head].first_valid_index(), domain]
                filter_comprehension_check(col_loc, condition, domain)

def filter_comprehension_check(col_loc, condition, domain):
    # Takes condition and checks whether responses match correct comprehension responses, returning an array of bools
    # True = FAIL comprehension check
    if "Authentic" in condition:
        mask = np.where((data[domain] == condition) & 
                       ((data.iloc[:, col_loc] == 2) | (data.iloc[:, col_loc + 1] == 2)),
                         True, False)
    else:
        mask = np.where((data[domain] == condition) & 
                       ((data.iloc[:, col_loc] == 2) | (data.iloc[:, col_loc + 1] == 1)),
                         True, False)
        
    # Shows in console number of participants who failed the question and the corresponding condition, in order of trial
    print(condition, np.count_nonzero(mask == True))

    data.drop(data.loc[mask].index, axis=0, inplace=True)

search_cols()
filter_duration()
filter_duplicate()
filter_fluency()
filter_incomplete_surveys()
filter_experimenter_data()
search_comprehension_cols()

data.to_csv("clean_data.csv", index=False)
