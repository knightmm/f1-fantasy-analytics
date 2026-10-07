from dotenv import load_dotenv
import os
import requests
from src.utils.races import get_completed_race_numbers
from src.transform_teams import (
    make_team_leaderboard_dataframe,
    make_team_race_dataframe,
    make_team_race_asset_dataframe,
    cast_team_race_dtypes,
    drop_user_team_column,
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

        # Transform raw leaderboard into processed team data
        team_leaderboard_df = make_team_leaderboard_dataframe(raw_data)

        team_race_with_assets = make_team_race_dataframe(
            team_leaderboard_df, raw_data, race_number
        )

        team_race_with_assets = cast_team_race_dtypes(team_race_with_assets)

        team_race_assets = make_team_race_asset_dataframe(team_race_with_assets)

        team_race = drop_user_team_column(team_race_with_assets)

        # Save processed data
        save_processed_csv(team_race, "team_race", race_number)
        save_processed_csv(team_race_assets, "team_race_asset", race_number)

        print(f"Saved processed team data for race {race_number}")


if __name__ == "__main__":
    main()