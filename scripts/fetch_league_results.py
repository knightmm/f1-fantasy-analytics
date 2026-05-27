from dotenv import load_dotenv
import os
import requests
from src.utils.races import get_completed_race_numbers
from src.transform_league import (
    make_league_standings_dataframe,
    make_league_standings_snapshot_dataframe,
    make_team_asset_snapshots_dataframe,
    cast_league_standings_dtypes,
    drop_team_assets_from_league_standings
)
from src.utils.paths import (
    raw_file_exists,
    load_raw_json,
    save_raw_json,
    save_processed_csv
)

# API
load_dotenv()
LEAGUE_ID = os.getenv("LEAGUE_ID")

def fetch_league_standings(race_number):
    url = f"https://fantasy.formula1.com/feeds/leaderboard/privateleague/list_2_{LEAGUE_ID}_{race_number}_1.json"
    
    r = requests.get(url)
    r.raise_for_status()
        
    return r.json()


# Orchestration Logic
def main():
    
    completed_races = get_completed_race_numbers()
    for race_number in completed_races:
        
        if raw_file_exists("league_standings", race_number):
            raw_data = load_raw_json("league_standings", race_number)
            print(f"Loaded existing League Standings JSON for race {race_number}")

        else:
            raw_data = fetch_league_standings(race_number)
            save_raw_json(raw_data, "league_standings", race_number)
            print(f"Saved raw League Standings JSON for race {race_number}")
        
        leaderboard_df = make_league_standings_dataframe(raw_data)
                
        league_standings_with_assets = make_league_standings_snapshot_dataframe(leaderboard_df, raw_data, race_number)
        
        league_standings_with_assets = cast_league_standings_dtypes(league_standings_with_assets)

        league_team_assets = make_team_asset_snapshots_dataframe(league_standings_with_assets)
        
        league_standings = drop_team_assets_from_league_standings(league_standings_with_assets)
        
        save_processed_csv(league_standings, "league_standings_snapshot", race_number)
        save_processed_csv(league_team_assets, "team_asset_snapshot", race_number)
        print(f"Saved processed league CSVs for race {race_number}")
        

if __name__ == "__main__":
    main()