from src.utils.races import get_completed_race_numbers
from src.utils.paths import (
    get_processed_file_path,
    load_detailed_team_raw,
    get_season_processed_file_path,
    save_processed_csv
)
import pandas as pd
from src.transform_detailed_teams import (
    make_team_chip_usage_dataframe,
    make_detailed_team_assets_dataframe
)

# 1. Chip Usage
# Get completed races + store latest race number
completed_races = get_completed_race_numbers()
latest_race = max(completed_races)

# Load latest processed public league standings to identify league teams
league_path = get_processed_file_path(
    "league_standings_snapshot",
    latest_race
)

league = pd.read_csv(league_path)

league_teams = league[
    ["user_guid", "team_no"]
].drop_duplicates()

# Load each team's raw detailed JSON for the latest race
chip_usage_dfs = []

for _, league_team in league_teams.iterrows():
    user_guid = league_team["user_guid"]
    team_no = int(league_team["team_no"])

    detailed_team_raw = load_detailed_team_raw(
        user_guid,
        team_no,
        latest_race
    )
    
    team = detailed_team_raw["Data"]["Value"]["userTeam"][0]
    
# Transform chip usage data for this team
    chip_usage = make_team_chip_usage_dataframe(team, user_guid)
    chip_usage_dfs.append(chip_usage)

# combine returned dataframes
team_chip_usage = pd.concat(chip_usage_dfs, ignore_index=True)

# check no team has used the same chip more than once
assert not team_chip_usage.duplicated(
    subset=["season", "user_guid", "team_no", "chip_id"]
).any(), "Duplicate chip usage found for the same team"

# save team_chip_usage_2026.csv
output_path = get_season_processed_file_path(
    "team_chip_usage",
    2026
)

team_chip_usage.to_csv(output_path, index=False)
print(f"Saved {output_path}")

# 2. Detailed team asset data

asset_dfs = []

for race_number in completed_races:
    for _, league_team in league_teams.iterrows():
        user_guid = league_team["user_guid"]
        team_no = int(league_team["team_no"])

        detailed_team_raw = load_detailed_team_raw(
            user_guid,
            team_no,
            race_number
        )

        team = detailed_team_raw["Data"]["Value"]["userTeam"][0]

        asset_df = make_detailed_team_assets_dataframe(
            team,
            user_guid,
            race_number
        )

        asset_dfs.append(asset_df)

detailed_team_assets = pd.concat(asset_dfs, ignore_index=True)

# Enrich existing team asset snapshots

for race_number in completed_races:
    team_assets = pd.read_csv(
        get_processed_file_path("team_asset_snapshot", race_number)
    )

    # Remove existing enrichment columns if the pipeline has already been run
    enrichment_columns = [
        "is_captain",
        "is_mg_captain",
        "player_position",
        "is_final",
    ]

    team_assets = team_assets.drop(
        columns=enrichment_columns,
        errors="ignore"
    )

    detailed_assets_race = detailed_team_assets[
        detailed_team_assets["race_number"] == race_number
    ].copy()

    # Make sure asset IDs have the same type
    team_assets["asset_id"] = team_assets["asset_id"].astype(str)
    detailed_assets_race["asset_id"] = detailed_assets_race["asset_id"].astype(str)

    # Keep only the columns needed for enrichment
    detailed_assets_race = detailed_assets_race[
        [
            "user_guid",
            "team_no",
            "asset_id",
            "is_captain",
            "is_mg_captain",
            "player_position",
            "is_final",
        ]
    ]

    enriched_team_assets = team_assets.merge(
        detailed_assets_race,
        on=["user_guid", "team_no", "asset_id"],
        how="left",
        validate="one_to_one"
    )

    # Check that every existing asset matched the detailed data. 0 and 1 will pass. NaN fails and indicates a missing left join
    assert enriched_team_assets["is_captain"].notna().all(), (
        f"Unmatched team assets found for race {race_number}"
    )

    # Save enriched snapshot
    save_processed_csv(
        enriched_team_assets,
        "team_asset_snapshot",
        race_number
    )

print(f"Enriched team asset snapshots for {len(completed_races)} races")