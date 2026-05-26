import pandas as pd
from datetime import datetime, timezone
from urllib.parse import unquote

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

def cast_league_standings_dtypes(league_standings):
    league_standings = league_standings.copy()
    
    league_standings["feed_time_utc"] = pd.to_datetime(league_standings["feed_time_utc"], format="%m/%d/%Y %I:%M:%S %p", utc=True)
    league_standings["retrieved_at_utc"] = pd.to_datetime(league_standings["retrieved_at_utc"], utc=True)
    
    int_cols = [
        "season",
        "race_number",
        "team_no",
        "race_rank",
        "trend"
    ]
    
    float_cols = ["race_points"]
    
    string_cols = [
        "user_guid",
        "team_name",
        "user_name"
    ]
    
    for col in int_cols:
        league_standings[col] = pd.to_numeric(league_standings[col], errors="coerce").astype("Int64")
    
    for col in float_cols:
        league_standings[col] = pd.to_numeric(league_standings[col], errors="coerce")  

    for col in string_cols:
        league_standings[col] = league_standings[col].astype(str)    
        
    return league_standings                                 
                                        

def make_team_assets_dataframe(league_standings_df):
    team_assets_df = league_standings_df.explode("user_team")

    team_assets_df = team_assets_df.rename(
        columns={
            "user_team": "asset_id"
        }
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

    team_assets_df["asset_id"] = team_assets_df["asset_id"].astype(str)

    return team_assets_df

def make_clean_league_standings_dataframe(league_standings_df):
    return league_standings_df.drop(columns=["user_team"])
