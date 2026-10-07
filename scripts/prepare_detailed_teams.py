from src.utils.races import get_completed_race_numbers
from src.utils.paths import (
    get_processed_file_path,
    load_detailed_team_raw,
    get_season_processed_file_path
)
import pandas as pd
from src.transform_detailed_teams import make_team_chip_usage_dataframe

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
