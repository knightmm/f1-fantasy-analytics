import pandas as pd
from datetime import datetime, timezone
from urllib.parse import unquote


def make_team_leaderboard_dataframe(raw_data):
    return pd.json_normalize(raw_data["Value"]["leaderboard"])


def make_team_race_dataframe(df, raw_data, race_number):
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

    team_race = df[
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
            "trend",
            "user_team",
        ]
    ]

    return team_race


def cast_team_race_dtypes(team_race):
    team_race = team_race.copy()

    team_race["feed_time_utc"] = pd.to_datetime(
        team_race["feed_time_utc"],
        format="%m/%d/%Y %I:%M:%S %p",
        utc=True
    )
    team_race["retrieved_at_utc"] = pd.to_datetime(
        team_race["retrieved_at_utc"],
        utc=True
    )

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
    ]

    for col in int_cols:
        team_race[col] = pd.to_numeric(
            team_race[col], errors="coerce"
        ).astype("Int64")

    for col in float_cols:
        team_race[col] = pd.to_numeric(
            team_race[col], errors="coerce"
        )

    for col in string_cols:
        team_race[col] = team_race[col].astype(str)

    return team_race


def make_team_race_asset_dataframe(team_race_df):
    team_assets_df = team_race_df.explode("user_team")

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
            "team_name",
            "asset_id",
        ]
    ]

    team_assets_df["asset_id"] = team_assets_df["asset_id"].astype(str)

    return team_assets_df


def drop_user_team_column(team_race_df):
    return team_race_df.drop(columns=["user_team"])