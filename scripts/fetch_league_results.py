from dotenv import load_dotenv
import os
import requests
import pandas as pd
from datetime import datetime, timezone
from urllib.parse import unquote
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
    url = f"https://fantasy.formula1.com/feeds/leaderboard/privateleague/list_2_{LEAGUE_ID}_{race_number}_1.json"
    
    r = requests.get(url)
    r.raise_for_status()
        
    return r.json()

def make_league_standings_dataframe(raw_data):
    return pd.json_normalize(raw_data["Value"]["leaderboard"])

def clean_league_standings_dataframe(df, raw_data, race_number):
    df = df.copy()
    
    df["team_name"] = df["team_name"].apply(unquote)
    df["feed_time_utc"] = raw_data["FeedTime"]["UTCTime"]
    df["retrieved_at_utc"] = datetime.now(timezone.utc)
    df["race_number"] = race_number
    df["season"] = 2026
    
    df = df.rename(
    columns={
        "cur_rank": "race_rank",
        "cur_points": "race_points",
        }
    )
    
    league_standings = df[
        [
            "season",
            "race_number",
            "feed_time_utc",
            "retrieved_at_utc",
            "user_guid",
            "team_no",
            "race_rank",
            "race_points",
            "team_name",
            "user_name",
            "trend",
            "user_team",
        ]
    ]

    return league_standings

def make_team_assets_dataframe(league_standings_df):
    team_assets_df = league_standings_df.explode("user_team")

    team_assets_df = team_assets_df.rename(
        columns={"user_team": "asset_id"}
    )

    team_assets_df = team_assets_df[
        [
            "season",
            "race_number",
            "user_guid",
            "team_no",
            "asset_id",
        ]
    ]

    return team_assets_df

def make_clean_league_standings_dataframe(league_standings_df):
    return league_standings_df.drop(columns=["user_team"])


# Orchestration Logic
def main():
    
    completed_races = get_completed_race_numbers()
    for race_number in completed_races:
        
        # Fix 1: Check feed time and if server time is more recent then update the file
        # Fix 2: Only reprocess if feed changed
        if raw_file_exists("league_standings", race_number):
            print(f"League Standings for Race {race_number} JSON already exists. Skipping.")
            continue
        
        raw_data = fetch_league_standings(race_number)
        save_raw_json(raw_data, "league_standings", race_number)
        print(f"Saved raw League Standings JSON for race {race_number}")
        
        leaderboard_df = make_league_standings_dataframe(raw_data)
        
        #df = cast_asset_dtypes(df)
        
        league_standings_with_assets = clean_league_standings_dataframe(leaderboard_df, raw_data, race_number)

        league_team_assets = make_team_assets_dataframe(league_standings_with_assets)
        
        league_standings = make_clean_league_standings_dataframe(league_standings_with_assets)
        
        save_processed_csv(league_standings, "league_standings", race_number)
        save_processed_csv(league_team_assets, "league_team_assets", race_number)
        print(f"Saved processed league CSVs for race {race_number}")
        

if __name__ == "__main__":
    main()