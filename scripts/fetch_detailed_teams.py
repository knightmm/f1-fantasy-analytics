import os
import pandas as pd
import requests
from dotenv import load_dotenv

from src.utils.races import get_completed_race_numbers
from src.utils.paths import (
    get_processed_file_path,
    detailed_team_raw_exists,
    save_detailed_team_raw
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

    response = requests.get(url, headers=headers)

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

    # Use the latest standings snapshot to identify league members
    latest_race = max(completed_races)

    standings_path = get_processed_file_path(
        "league_standings_snapshot",
        latest_race
    )

    standings = pd.read_csv(standings_path)

    league_members = standings[
        ["user_guid", "team_no"]
    ].drop_duplicates()

    # Temporary test: first two league members, race 1 only
    #test_members = league_members.head(2)
    #test_races = [1]

    for race_number in completed_races:
        for _, member in league_members.iterrows():
            user_guid = member["user_guid"]
            team_no = int(member["team_no"])

            if detailed_team_raw_exists(
                user_guid,
                team_no,
                race_number
            ):
                print(
                    f"Detailed raw team data already exists: "
                    f"team {team_no}, race {race_number}"
                )
                continue

            raw_data = fetch_detailed_team(
                user_guid,
                team_no,
                race_number
            )

            save_detailed_team_raw(
                raw_data,
                user_guid,
                team_no,
                race_number
            )

            print(
                f"Saved detailed raw team data: "
                f"team {team_no}, race {race_number}"
            )


if __name__ == "__main__":
    main()