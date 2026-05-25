import requests
import os
import json
from src.utils.races import get_completed_race_numbers
from src.utils.paths import (
    get_raw_file_path,
    raw_file_exists
)
from src.transform_assets import (
    make_assets_dataframe, 
    rename_asset_columns, 
    cast_asset_dtypes, 
    make_constructors_dataframe, 
    make_drivers_dataframe
    )

# API
def fetch_assets(race_number):
    url = f"https://fantasy.formula1.com/feeds/drivers/{race_number}_en.json"
    r = requests.get(url)
    r.raise_for_status()
    
    data = r.json()
    return data

# Save Raw JSON
def save_raw_json(data, race_number):
    file_path = get_raw_file_path(race_number)
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
        

def save_entity_csv(data, entity_name, race_number):
    csv_save_path = os.path.join("data", "processed", f"{entity_name}_race_{race_number}.csv")
    data.to_csv(csv_save_path, index=False)


# Orchestration Logic
def main():
    
    completed_races = get_completed_race_numbers()
    for race_number in completed_races:
        
        # Fix 1: Check feed time and if server time is more recent then update the file
        # Fix 2: Only reprocess if feed changed
        if raw_file_exists("assets", race_number):
            print(f"Assets Race {race_number} JSON already exists. Skipping.")
            continue
        
        data = fetch_assets(race_number)
        save_raw_json(data, race_number)
        print(f"Saved raw Assets JSON for race {race_number}")
        
        df = make_assets_dataframe(data, race_number)
        df = rename_asset_columns(df)
        df = cast_asset_dtypes(df)
        
        constructors_df = make_constructors_dataframe(df)
        save_entity_csv(constructors_df, "constructors", race_number)
        print(f"Saved Constructors CSV for race {race_number}")
        
        drivers_df = make_drivers_dataframe(df)
        save_entity_csv(drivers_df, "drivers", race_number)
        print(f"Saved Drivers CSV for race {race_number}")

if __name__ == "__main__":
    main()