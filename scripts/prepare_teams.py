from src.utils.races import get_completed_race_numbers
from src.utils.paths import load_raw_json, save_processed_csv
from src.transform_teams import (
    make_team_leaderboard_dataframe,
    make_team_race_dataframe,
    make_team_race_asset_dataframe,
    cast_team_race_dtypes,
    drop_user_team_column,
)


def main():
    completed_races = get_completed_race_numbers()

    for race_number in completed_races:
        raw_data = load_raw_json("league_standings", race_number)

        leaderboard = make_team_leaderboard_dataframe(raw_data)

        team_race_with_assets = make_team_race_dataframe(
            leaderboard, raw_data, race_number
        )
        team_race_with_assets = cast_team_race_dtypes(
            team_race_with_assets
        )

        team_assets = make_team_race_asset_dataframe(
            team_race_with_assets
        )
        team_race = drop_user_team_column(team_race_with_assets)

        save_processed_csv(team_race, "team_race", race_number)
        save_processed_csv(team_assets, "team_race_asset", race_number)

    print(
        f"Team preparation complete: {len(completed_races)} races processed, "
        f"{len(completed_races) * 2} CSVs saved."
    )


if __name__ == "__main__":
    main()