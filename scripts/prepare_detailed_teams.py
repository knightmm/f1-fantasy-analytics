import pandas as pd

from src.utils.races import get_completed_race_numbers
from src.utils.paths import (
    get_processed_file_path,
    load_detailed_team_raw,
    get_season_processed_file_path,
    save_processed_csv,
)
from src.transform_detailed_teams import (
    make_team_chip_usage_dataframe,
    make_detailed_team_assets_dataframe,
    make_detailed_team_race_dataframe,
)


def main():
    completed_races = get_completed_race_numbers()
    latest_race = max(completed_races)

    # 1. Chip usage for teams in the latest standings
    team_race = pd.read_csv(
        get_processed_file_path("team_race", latest_race)
    )

    teams = team_race[
        ["user_guid", "team_no"]
    ].drop_duplicates()

    chip_usage_dfs = []

    for _, fantasy_team in teams.iterrows():
        user_guid = fantasy_team["user_guid"]
        team_no = int(fantasy_team["team_no"])

        detailed_team_raw = load_detailed_team_raw(
            user_guid,
            team_no,
            latest_race,
        )

        team = detailed_team_raw["Data"]["Value"]["userTeam"][0]

        chip_usage = make_team_chip_usage_dataframe(team, user_guid)
        chip_usage_dfs.append(chip_usage)

    team_chip_usage = pd.concat(chip_usage_dfs, ignore_index=True)

    if team_chip_usage.duplicated(
        subset=["season", "user_guid", "team_no", "chip_id"]
    ).any():
        raise ValueError("Duplicate chip usage found for the same team")

    output_path = get_season_processed_file_path(
        "team_chip_usage",
        2026,
    )

    team_chip_usage.to_csv(output_path, index=False)
    print(f"Prepared chip usage data: {len(team_chip_usage)} records")

    # 2. Detailed team asset data
    asset_dfs = []

    for race_number in completed_races:
        # Historical races may contain teams absent from the latest standings.
        race_teams = pd.read_csv(
            get_processed_file_path("team_race", race_number)
        )[["user_guid", "team_no"]].drop_duplicates()

        for _, fantasy_team in race_teams.iterrows():
            user_guid = fantasy_team["user_guid"]
            team_no = int(fantasy_team["team_no"])

            detailed_team_raw = load_detailed_team_raw(
                user_guid,
                team_no,
                race_number,
            )

            team = detailed_team_raw["Data"]["Value"]["userTeam"][0]

            asset_df = make_detailed_team_assets_dataframe(
                team,
                user_guid,
                race_number,
            )

            asset_dfs.append(asset_df)

    detailed_team_assets = pd.concat(asset_dfs, ignore_index=True)

    # Enrich existing team race asset data
    asset_enrichment_columns = [
        "is_captain",
        "is_mg_captain",
        "player_position",
        "is_final",
    ]

    for race_number in completed_races:
        team_assets = pd.read_csv(
            get_processed_file_path("team_race_asset", race_number)
        )

        team_assets = team_assets.drop(
            columns=asset_enrichment_columns,
            errors="ignore",
        )

        detailed_assets_race = detailed_team_assets[
            detailed_team_assets["race_number"] == race_number
        ].copy()

        # Make sure asset IDs have the same type.
        team_assets["asset_id"] = team_assets["asset_id"].astype(str)
        detailed_assets_race["asset_id"] = (
            detailed_assets_race["asset_id"].astype(str)
        )

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
            validate="one_to_one",
        )

        # A missing captain flag indicates an unmatched asset.
        if not enriched_team_assets["is_captain"].notna().all():
            raise ValueError(
                f"Unmatched team assets found for race {race_number}"
            )

        save_processed_csv(
            enriched_team_assets,
            "team_race_asset",
            race_number,
        )

    print(f"Enriched team race assets for {len(completed_races)} races")

    # 3. Detailed team financial and transfer data
    race_dfs = []

    for race_number in completed_races:
        race_teams = pd.read_csv(
            get_processed_file_path("team_race", race_number)
        )[["user_guid", "team_no"]].drop_duplicates()

        for _, fantasy_team in race_teams.iterrows():
            user_guid = fantasy_team["user_guid"]
            team_no = int(fantasy_team["team_no"])

            detailed_team_raw = load_detailed_team_raw(
                user_guid,
                team_no,
                race_number,
            )

            team = detailed_team_raw["Data"]["Value"]["userTeam"][0]

            race_df = make_detailed_team_race_dataframe(
                team,
                user_guid,
                race_number,
            )

            race_dfs.append(race_df)

    detailed_team_races = pd.concat(race_dfs, ignore_index=True)

    # Enrich existing team race data
    race_enrichment_columns = [
        "recorded_asset_value",
        "remaining_budget",
        "recorded_total_budget",
        "transfers_made",
        "free_transfers_remaining",
    ]

    for race_number in completed_races:
        team_race = pd.read_csv(
            get_processed_file_path("team_race", race_number)
        )

        team_race = team_race.drop(
            columns=race_enrichment_columns,
            errors="ignore",
        )

        detailed_race = detailed_team_races[
            detailed_team_races["race_number"] == race_number
        ]

        enriched_team_race = team_race.merge(
            detailed_race,
            on=["season", "race_number", "user_guid", "team_no"],
            how="left",
            validate="one_to_one",
        )

        if not enriched_team_race["remaining_budget"].notna().all():
            raise ValueError(
                f"Unmatched detailed teams found for race {race_number}"
            )

        save_processed_csv(
            enriched_team_race,
            "team_race",
            race_number,
        )

    print(f"Enriched team race data for {len(completed_races)} races")


if __name__ == "__main__":
    main()