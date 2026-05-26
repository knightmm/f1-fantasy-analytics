import os
import json

def get_raw_file_path(dataset_name, race_number):
    return os.path.join("data", "raw", f"{dataset_name}_race_{race_number}.json")
    
def raw_file_exists(dataset_name, race_number):
    file_path = get_raw_file_path(dataset_name, race_number)
    
    return os.path.exists(file_path)

def load_raw_json(dataset_name, race_number):

    path = os.path.join("data", "raw", f"{dataset_name}_{race_number}.json")

    with open(path, "r") as f:
        data = json.load(f)

    return data

def save_raw_json(data, dataset_name, race_number):
    file_path = get_raw_file_path(dataset_name, race_number)
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
        
        
def save_processed_csv(data, dataset_name, race_number):
    csv_save_path = os.path.join("data", "processed", f"{dataset_name}_race_{race_number}.csv")
    data.to_csv(csv_save_path, index=False)