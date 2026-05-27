import pandas as pd
from datetime import datetime, timezone

# Transformation/Save to CSV
def make_assets_dataframe(data, race_number):
    # Normalize data in the value subdictionary, append API feed timestamp, retrieved time, race number and season columns
    df = pd.json_normalize(data["Data"]["Value"])
    
    df["feed_time_utc"] = data["Data"]["FeedTime"]["UTCTime"]
    df["retrieved_at_utc"] = datetime.now(timezone.utc)
    df["race_number"] = race_number
    df["season"] = 2026
    
    # Rearrange columns
    cols_to_front = ["season", "race_number", "feed_time_utc", "retrieved_at_utc"]
    remaining_cols = [col for col in df.columns if col not in cols_to_front]
    df = df[cols_to_front + remaining_cols]
    
    return df

    # Rename columns
def rename_asset_columns(df):
    df = df.rename(columns=
            {    
                    "PlayerId": "asset_id",
                    "Skill": "skill",
                    "PositionName": "asset_type",
                    "Value": "value",
                    "TeamId": "team_id",
                    "FUllName": "full_name",
                    "DisplayName": "display_name",
                    "IsActive": "is_active",
                    "DriverTLA": "driver_tla",
                    "OverallPpints": "overall_points",
                    "GamedayPoints": "gameday_points",
                    "SelectedPercentage": "selected_percentage",
                    "CaptainSelectedPercentage": "captain_selected_percentage",
                    "OldPlayerValue": "old_asset_value",
                    "BestRaceFinished": "best_race_finished",
                    "HigestGridStart": "highest_grid_start",
                    "HigestChampFinish": "highest_champ_finish",
                    "FastestPitstopAward": "fastest_pitstop_award",
                    "BestRaceFinishCount": "best_race_finish_count",
                    "HighestGridStartCount": "highest_grid_start_count",
                    "HighestChampFinishCount": "highest_champ_finish_count",
                    "FastestPitstopAwardCount": "fastest_pitstop_award_count",
                    "QualifyingPoints": "qualifying_points",
                    "RacePoints": "race_points",
                    "SprintPoints": "sprint_points",
                    "NoNegativePoints": "no_negative_points",
                    "F1PlayerId": "driver_team_id",
                    "FirstName": "driver_team_first_name",
                    "LastName": "driver_team_last_name",
                    "SessionWisePoints": "all_session_points",
                    "old_Value": "old_value",
                    "new_value": "new_value",
                    "ProjectedGamedayPoints": "projected_gameday_points",
                    "ProjectedNoNegativePoints": "projected_no_negative_points",
                    "ProjectedOverallPpints": "projected_overall_points",
                    "AdditionalStats.fastest_lap_pts": "fastest_lap_points",
                    "AdditionalStats.dotd_pts": "dotd_points",
                    "AdditionalStats.overtaking_pts": "overtake_points",
                    "AdditionalStats.q3_finishes_pts": "q3_finishes_points",
                    "AdditionalStats.top10_race_position_pts": "top10_race_position_points",
                    "AdditionalStats.top8_sprint_position_pts": "top8_sprint_position_points",
                    "AdditionalStats.total_position_pts": "total_position_points",
                    "AdditionalStats.total_position_gained_lost": "total_positions_gained_lost_points",
                    "AdditionalStats.total_dnf_dq_pts": "total_dnf_dq_points",
                    "AdditionalStats.value_for_money": "value_for_money"
              }
              )
    
    df = df.drop(columns=["old_value", "new_value"], errors="ignore")

    return df
    
    
    # Correct data types
def cast_asset_dtypes(df):
    df["feed_time_utc"] = pd.to_datetime(df["feed_time_utc"], format="%m/%d/%Y %I:%M:%S %p", utc=True)
    df["retrieved_at_utc"] = pd.to_datetime(df["retrieved_at_utc"], utc=True)
    
    int_cols = [
        "season",
        "race_number",
        "asset_id",
        "skill",
        "team_id",
        "is_active",
        "gameday_points",
        "best_race_finish_count",
        "highest_grid_start_count",
        "highest_champ_finish_count",
        "fastest_pitstop_award_count",
        "driver_team_id",
    ]

    float_cols = [
        "value",
        "overall_points",
        "selected_percentage",
        "captain_selected_percentage",
        "old_asset_value",
        "best_race_finished",
        "highest_grid_start",
        "highest_champ_finish",
        "fastest_pitstop_award",
        "qualifying_points",
        "race_points",
        "sprint_points",
        "no_negative_points",
        "projected_gameday_points",
        "projected_no_negative_points",
        "projected_overall_points",
        "fastest_lap_points",
        "dotd_points",
        "overtake_points",
        "q3_finishes_points",
        "top10_race_position_points",
        "top8_sprint_position_points",
        "total_position_points",
        "total_positions_gained_lost_points",
        "total_dnf_dq_points",
        "value_for_money",
    ]
    
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
        
    return df

