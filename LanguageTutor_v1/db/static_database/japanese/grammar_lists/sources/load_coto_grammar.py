import json
import pandas as pd

# Global file paths
CSV_PATH = 'n5_grammar.csv'  # Replace with the actual CSV file path
JSON_PATH = '../n5.json'  # Replace with the actual JSON file path

def update_json_from_csv(csv_path, json_path):
    """
    Updates a JSON file with data from a CSV file.
    The CSV file must have 'Grammar Point' and 'English' columns.
    
    :param csv_path: Path to the CSV file
    :param json_path: Path to the JSON file
    """
    # Load the CSV file and extract relevant columns
    csv_data = pd.read_csv(csv_path, skiprows=4, usecols=[0, 4], names=['Grammar Point', 'English'], header=0)
    csv_data = csv_data.dropna()  # Remove rows with missing data

    # Load existing JSON data or initialize as an empty dictionary
    try:
        with open(json_path, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
    except FileNotFoundError:
        json_data = {}

    # Update JSON data with information from the CSV file
    for _, row in csv_data.iterrows():
        grammar_point = row['Grammar Point']
        meaning = row['English']
        
        # Only add the entry if the grammar point is not already in the JSON
        if grammar_point not in json_data:
            json_data[grammar_point] = {"meaning": meaning}

    # Write updated JSON data back to the file
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=4)

# Execute the function
update_json_from_csv(CSV_PATH, JSON_PATH)
