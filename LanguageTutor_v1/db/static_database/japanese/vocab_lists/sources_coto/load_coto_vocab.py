import json
import pandas as pd

# Global file paths
CSV_PATH = 'n5.csv'  # Replace with the actual CSV file path
JSON_PATH = '../n5.json'  # Replace with the actual JSON file path

def update_json_from_csv(csv_path, json_path):
    """
    Updates a JSON file with data from a CSV file.
    If 'Kanji' is empty, it uses 'Hiragana' as the key.
    
    :param csv_path: Path to the CSV file
    :param json_path: Path to the JSON file
    """
    # Load the CSV file and extract relevant columns
    csv_data = pd.read_csv(csv_path, skiprows=4, usecols=[0, 1, 2], names=['Kanji', 'Hiragana', 'English'], header=0)
    csv_data = csv_data.dropna(subset=['English'])  # Remove rows where 'English' is missing

    # Load existing JSON data or initialize as an empty dictionary
    try:
        with open(json_path, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
    except FileNotFoundError:
        json_data = {}

    # Update JSON data with information from the CSV file
    for _, row in csv_data.iterrows():
        key = row['Kanji'] if pd.notna(row['Kanji']) else row['Hiragana']
        meaning = row['English']
        json_data[key] = {"meaning": meaning}

    # Write updated JSON data back to the file
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=4)

# Execute the function
update_json_from_csv(CSV_PATH, JSON_PATH)

