import requests
import os
import json
import pandas as pd
from datetime import date, datetime, timezone


# Helper Functions
def get_completed_race_numbers():
    races_csv = os.path.join("data", "reference", "races_2026.csv")
    races = pd.read_csv(races_csv)
    races["race_date"] = pd.to_datetime(races["race_date"]).dt.date
    
    today = date.today()
    completed_races = races[races["race_date"] < today]
    return completed_races["race_number"].sort_values().tolist()

def get_raw_file_path(race_number):
    return os.path.join("data", "raw", f"assets_race_{race_number}.json")
    
def raw_file_exists(race_number):
    file_path = get_raw_file_path(race_number)
    return os.path.exists(file_path)

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
        

# Transformation/Save to CSV
def make_assets_dataframe(data, race_number):
    # Normalize data in the value subdictionary, append API feed timestamp, retrieved time, race number and season columns
    df = pd.json_normalize(data["Data"]["Value"])
    df["feed_time_utc"] = data["Data"]["FeedTime"]["UTCTime"]
    df["retrieved_at_utc"] = datetime.now(timezone.utc)
    df["race_number"] = race_number
    df["season"] = 2026
    
    # Put season, race number and feed time at the front
    cols_to_front = ["season", "race_number", "feed_time_utc", "retrieved_at_utc"]
    remaining_cols = [col for col in df.columns if col not in cols_to_front]
    df = df[cols_to_front + remaining_cols]
    
    # Correct data types
    df["feed_time_utc"] = pd.to_datetime(df["feed_time_utc"], format="%m/%d/%Y %I:%M:%S %p", utc=True)
    df["retrieved_at_utc"] = pd.to_datetime(df["retrieved_at_utc"], utc=True)
    int_cols = [
        "season",
        "race_number",
        "GamedayPoints",
        "BestRaceFinished",
        "HigestGridStart",
        "BestRaceFinishCount",
        "HighestGridStartCount",
        "HighestChampFinishCount",
        "FastestPitstopAwardCount",
    ]
    float_cols = [
        "Value",
        "OverallPpints",
        "QualifyingPoints",
        "RacePoints",
        "SprintPoints",
        "NoNegativePoints",
        "ProjectedGamedayPoints",
        "ProjectedNoNegativePoints",
        "ProjectedOverallPpints",
        "SelectedPercentage",
        "CaptainSelectedPercentage",
        "OldPlayerValue",
        "FastestPitstopAward",
        "old_Value",
        "new_value",
        "HigestChampFinish",
    ]
    
    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in float_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    return df

def make_constructors_dataframe(df):
    constructor_filter = df["PositionName"] == "CONSTRUCTOR"
    constructors_df = df[constructor_filter].copy()
    
    constructor_drop_cols = ['TeamName', 'Status', 'DriverReference', 'CountryName']
    constructors_df = constructors_df.drop(columns=constructor_drop_cols)
    return constructors_df

def make_drivers_dataframe(df):
    drivers_filter = df["PositionName"] == "DRIVER"
    drivers_df = df[drivers_filter].copy()
    return drivers_df

def save_entity_csv(data, entity_name, race_number):
    csv_save_path = os.path.join("data", "processed", f"{entity_name}_race_{race_number}.csv")
    data.to_csv(csv_save_path, index=False)


# Orchestration Logic
def main():
    
    completed_races = get_completed_race_numbers()
    for race_number in completed_races:
        
        # Fix 1: Check feed time and if server time is more recent then update the file
        # Fix 2: Only reprocess if feed changed
        if raw_file_exists(race_number):
            print(f"Race {race_number} JSON already exists. Skipping.")
            continue
        
        data = fetch_assets(race_number)
        save_raw_json(data, race_number)
        print(f"Saved raw JSON for race {race_number}")
        
        df = make_assets_dataframe(data, race_number)
        
        constructors_df = make_constructors_dataframe(df)
        save_entity_csv(constructors_df, "constructors", race_number)
        print(f"Saved Constructors CSV for race {race_number}")
        
        drivers_df = make_drivers_dataframe(df)
        save_entity_csv(drivers_df, "drivers", race_number)
        print(f"Saved Drivers CSV for race {race_number}")

if __name__ == "__main__":
    main()