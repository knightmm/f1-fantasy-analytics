import requests

from src.utils.races import get_completed_race_numbers
from src.utils.paths import raw_file_exists, save_raw_json


def fetch_assets(race_number):
    url = f"https://fantasy.formula1.com/feeds/drivers/{race_number}_en.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def main():
    completed_races = get_completed_race_numbers()

    # Completed races plus the next race's price feed
    asset_races = range(1, max(completed_races) + 2)

    fetched = 0
    skipped = 0

    for race_number in asset_races:
        if raw_file_exists("asset_snapshot", race_number):
            skipped += 1
            continue

        data = fetch_assets(race_number)
        save_raw_json(data, "asset_snapshot", race_number)
        fetched += 1

    print(
        f"Asset fetch complete: {len(asset_races)} races checked, "
        f"{fetched} fetched, {skipped} already saved."
    )


if __name__ == "__main__":
    main()
