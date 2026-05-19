import requests
import os
import json
import pandas as pd

# when loop logic is included then move this into the fetch_assets function
#url = "https://fantasy.formula1.com/feeds/drivers/5_en.json"
#race_number = int(re.search(r"drivers/(\d+)_", url).group(1))

# helper functions
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

# saving the JSON file as is before processing
def save_raw_json(data, race_number):
    file_path = get_raw_file_path(race_number)
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
        

# Transformation/Save to CSV
def make_assets_dataframe(data, race_number):
    # normalizing the data in the value subdictionary, appending API feed timestamp and race number columns
    df = pd.json_normalize(data["Data"]["Value"])
    df["feed_time_utc"] = data["Data"]["FeedTime"]["UTCTime"]
    df["race_number"] = race_number
    # put race number and feed time at the front
    cols_to_front = ["race_number", "feed_time_utc"]
    remaining_cols = [col for col in df.columns if col not in cols_to_front]
    df = df[cols_to_front + remaining_cols]
    # correct data type of race_number and utc time
    df["race_number"] = df["race_number"].astype(int)
    df["feed_time_utc"] = pd.to_datetime(df["feed_time_utc"], format="%m/%d/%Y %I:%M:%S %p", utc=True)
    return df

def make_constructors_dataframe(df):
    constructor_filter = df["PositionName"] == "CONSTRUCTOR"
    constructors_df = df[constructor_filter].copy()
    constructor_drop_cols = ['TeamName', 'Status', 'DriverReference', 'CountryName']
    constructors_df = constructors_df.drop(columns=constructor_drop_cols)
    return constructors_df

def save_entity_csv(constructors_df, entity_name, race_number):
    csv_save_path = os.path.join("data", "processed", f"{entity_name}_race_{race_number}.csv")
    constructors_df.to_csv(csv_save_path, index=False)


# orchestration logic
def main():
    
    # update range based on current race, or later improve logic
    for race_number in range(1,6):
        
        # need to fix this logic so that if the JSON already exists the later steps and CSVs are still done
        if raw_file_exists(race_number):
            print(f"Race {race_number} JSON already exists. Skipping.")
            continue
        
        data = fetch_assets(race_number)
        save_raw_json(data, race_number)
        
        print(f"Saved JSON for race {race_number}")
        df = make_assets_dataframe(data, race_number)
        constructors_df = make_constructors_dataframe(df)
        save_entity_csv(constructors_df, "constructors", race_number)
        print(f"Saved Constructors CSV for race {race_number}")

if __name__ == "__main__":
    main()