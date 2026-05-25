from dotenv import load_dotenv
import os
import requests
from src.utils.races import get_completed_race_numbers
from src.utils.paths import (
    raw_file_exists,
    save_raw_json,
    save_processed_csv
)

# API
load_dotenv()
LEAGUE_ID = os.getenv("LEAGUE_ID")

def fetch_league_standings(race_number):
    # target league is 4436407
    url = f"https://fantasy.formula1.com/feeds/leaderboard/privateleague/list_2_{LEAGUE_ID}_{race_number}_1.json"
    
    r = requests.get(url)
    r.raise_for_status()
        
    data = r.json()
    return data


# Orchestration Logic
def main():
    
    completed_races = get_completed_race_numbers()
    for race_number in completed_races:
        
        # Fix 1: Check feed time and if server time is more recent then update the file
        # Fix 2: Only reprocess if feed changed
        if raw_file_exists("league_standings", race_number):
            print(f"League Standings for Race {race_number} JSON already exists. Skipping.")
            continue
        
        data = fetch_league_standings(race_number)
        save_raw_json(data, "league_standings", race_number)
        print(f"Saved raw League Standings JSON for race {race_number}")
        
        #df = make_assets_dataframe(data, race_number)
        #df = rename_asset_columns(df)
        #df = cast_asset_dtypes(df)
        
        #league_standings_df = make_constructors_dataframe(df)
        #save_processed_csv(league_standings_df, "league_standings", race_number)
        #print(f"Saved League Standings CSV for race {race_number}")
        

if __name__ == "__main__":
    main()