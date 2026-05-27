import sqlite3
import pandas as pd
import os

from src.utils.database import load_csvs_to_table


def main():
    
    DATABASE_PATH = os.path.join("data", "f1_fantasy.db")
    PROCESSED_DIR = os.path.join("data", "processed")

    with sqlite3.connect(DATABASE_PATH) as con:

        load_csvs_to_table(
            PROCESSED_DIR,
            "assets_race_",
            "assets_race_snapshots",
            con,
        )

        load_csvs_to_table(
            PROCESSED_DIR,
            "league_standings_race_",
            "league_standings",
            con,
        )

        load_csvs_to_table(
            PROCESSED_DIR,
            "league_team_assets_race_",
            "league_team_assets",
            con,
        )

        races_filepath = os.path.join("data", "reference", "races_2026.csv")

        races_df = pd.read_csv(races_filepath)
        races_df["race_date"] = pd.to_datetime(races_df["race_date"], utc=True)

        races_df.to_sql("races", con, if_exists="replace", index=False)

        print("Database load complete.")


if __name__ == "__main__":
    main()