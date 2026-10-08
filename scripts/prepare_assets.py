from src.utils.races import get_completed_race_numbers
from src.utils.paths import load_raw_json, save_processed_csv
from src.transform_assets import (
    make_assets_dataframe,
    rename_asset_columns,
    cast_asset_dtypes,
)


def main():
    completed_races = get_completed_race_numbers()

    # Use the same race coverage as the fetch stage
    asset_races = range(1, max(completed_races) + 2)

    for race_number in asset_races:
        data = load_raw_json("asset_snapshot", race_number)

        df = make_assets_dataframe(data, race_number)
        df = rename_asset_columns(df)
        df = cast_asset_dtypes(df)

        save_processed_csv(df, "asset_race", race_number)

    print(f"Asset preparation complete: {len(asset_races)} CSVs saved.")


if __name__ == "__main__":
    main()