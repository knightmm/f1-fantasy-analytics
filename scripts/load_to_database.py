
import sqlite3
import pandas as pd
import os

from src.utils.database import load_csvs_to_table
from src.validate_database import validate_database


def main():
    DATABASE_PATH = os.path.join("data", "f1_fantasy.db")
    PROCESSED_DIR = os.path.join("data", "processed")

    with sqlite3.connect(DATABASE_PATH) as con:

        load_csvs_to_table(
            PROCESSED_DIR,
            "asset_race_",
            "asset_race",
            con,
        )

        load_csvs_to_table(
            PROCESSED_DIR,
            "team_race_",
            "team_race",
            con,
        )

        load_csvs_to_table(
            PROCESSED_DIR,
            "team_race_asset_",
            "team_race_asset",
            con,
        )

        # Load team chip usage
        chip_usage_filepath = os.path.join(
            PROCESSED_DIR, "team_chip_usage_2026.csv"
        )

        chip_usage_df = pd.read_csv(chip_usage_filepath)
        chip_usage_df.to_sql(
            "team_chip_usage",
            con,
            if_exists="replace",
            index=False,
        )
        print(f"Loaded team_chip_usage table: {len(chip_usage_df)} rows")

        # Load race reference data
        races_filepath = os.path.join("data", "reference", "races_2026.csv")

        races_df = pd.read_csv(races_filepath)
        races_df["race_date"] = pd.to_datetime(races_df["race_date"], utc=True)

        races_df.to_sql("races", con, if_exists="replace", index=False)
        print(f"Loaded races table: {len(races_df)} rows")

        # Load chip reference data
        chips_filepath = os.path.join("data", "reference", "chips_2026.csv")

        chips_df = pd.read_csv(chips_filepath)
        chips_df.to_sql("chips", con, if_exists="replace", index=False)
        print(f"Loaded chips table: {len(chips_df)} rows")

        validate_database(con)
        print("Database load and validation complete.")

if __name__ == "__main__":
    main()
