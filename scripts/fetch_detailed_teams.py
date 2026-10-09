
import os
import pandas as pd
import requests
from dotenv import load_dotenv

from src.utils.races import get_completed_race_numbers
from src.utils.paths import (
    get_processed_file_path,
    detailed_team_raw_exists,
    save_detailed_team_raw,
)


# Authenticated API call
load_dotenv()


def fetch_detailed_team(user_guid, team_no, race_number):
    url = (
        "https://fantasy.formula1.com/services/user/opponentteam/"
        f"opponentgamedayplayerteamget/1/"
        f"{user_guid}/{team_no}/{race_number}/1"
    )

    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": "https://fantasy.formula1.com/",
        "user-agent": os.getenv("F1_USER_AGENT"),
        "cookie": os.getenv("F1_COOKIE"),
    }

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 401:
        raise RuntimeError(
            "F1 authentication failed (401). "
            "Refresh F1_COOKIE in the .env file."
        )

    response.raise_for_status()
    return response.json()


# Orchestration logic
def main():
    completed_races = get_completed_race_numbers()

    fetched = 0
    skipped = 0
    total_team_race_records = 0

    for race_number in completed_races:
        # Use the participants recorded for this specific race.
        standings_path = get_processed_file_path(
            "team_race",
            race_number,
        )

        standings = pd.read_csv(standings_path)

        race_teams = standings[
            ["user_guid", "team_no"]
        ].drop_duplicates()

        total_team_race_records += len(race_teams)

        for _, member in race_teams.iterrows():
            user_guid = member["user_guid"]
            team_no = int(member["team_no"])

            if detailed_team_raw_exists(
                user_guid, team_no, race_number
            ):
                skipped += 1
                continue

            raw_data = fetch_detailed_team(
                user_guid,
                team_no,
                race_number,
            )

            save_detailed_team_raw(
                raw_data,
                user_guid,
                team_no,
                race_number,
            )

            fetched += 1

    print(
        f"Detailed team fetch complete: "
        f"{total_team_race_records} team/race records "
        f"across {len(completed_races)} races, "
        f"{fetched} fetched, {skipped} already saved."
    )


if __name__ == "__main__":
    main()
