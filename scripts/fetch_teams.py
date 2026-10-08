import os
import requests
from dotenv import load_dotenv

from src.utils.races import get_completed_race_numbers
from src.utils.paths import raw_file_exists, save_raw_json

load_dotenv()
LEAGUE_ID = os.getenv("LEAGUE_ID")


def fetch_league_standings(race_number):
    url = (
        "https://fantasy.formula1.com/feeds/leaderboard/privateleague/"
        f"list_2_{LEAGUE_ID}_{race_number}_1.json"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def main():
    completed_races = get_completed_race_numbers()

    fetched = 0
    skipped = 0

    for race_number in completed_races:
        if raw_file_exists("league_standings", race_number):
            skipped += 1
            continue

        raw_data = fetch_league_standings(race_number)
        save_raw_json(raw_data, "league_standings", race_number)
        fetched += 1

    print(
        f"Team fetch complete: {len(completed_races)} races checked, "
        f"{fetched} fetched, {skipped} already saved."
    )


if __name__ == "__main__":
    main()