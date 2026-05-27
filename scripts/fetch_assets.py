# fetch_assets.py

import requests
from src.utils.races import get_completed_race_numbers
from src.utils.paths import (
    raw_file_exists,
    load_raw_json,
    save_raw_json,
    save_processed_csv,
)
from src.transform_assets import (
    make_assets_dataframe,
    rename_asset_columns,
    cast_asset_dtypes,
)


def fetch_assets(race_number):
    url = f"https://fantasy.formula1.com/feeds/drivers/{race_number}_en.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


def main():
    completed_races = get_completed_race_numbers()

    # Fetch completed races + next price feed
    asset_snapshot_races = range(1, max(completed_races) + 2)

    for race_number in asset_snapshot_races:
        if raw_file_exists("assets", race_number):
            data = load_raw_json("assets", race_number)
            print(f"Loaded existing Assets Race {race_number} JSON")
        else:
            data = fetch_assets(race_number)
            save_raw_json(data, "assets", race_number)
            print(f"Saved raw Assets JSON for race {race_number}")

        df = make_assets_dataframe(data, race_number)
        df = rename_asset_columns(df)
        df = cast_asset_dtypes(df)

        save_processed_csv(df, "assets", race_number)
        print(f"Saved Assets CSV for race {race_number}")


if __name__ == "__main__":
    main()