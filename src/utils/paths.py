import os

def get_raw_file_path(dataset_name, race_number):
    return os.path.join("data", "raw", f"{dataset_name}_race_{race_number}.json")
    
def raw_file_exists(dataset_name, race_number):
    file_path = get_raw_file_path(dataset_name, race_number)
    
    return os.path.exists(file_path)