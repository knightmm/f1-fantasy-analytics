import sqlite3
import pandas as pd
import os

# Define Paths
DATABASE_PATH = os.path.join("data", "f1_fantasy.db")
PROCESSED_DIR = os.path.join("data", "processed")

processed_files = os.listdir(PROCESSED_DIR)

# Connect to SQLite
con = sqlite3.connect(DATABASE_PATH)

    # Find Driver CSVs
driver_files = []

for file in processed_files:
    if file.startswith("drivers_race_"):
        driver_files.append(file)
driver_files.sort()
        
    # Read Driver + Create Dataframe
driver_dfs = []

for file in driver_files:
    filepath = os.path.join(PROCESSED_DIR, file) 
    df = pd.read_csv(filepath)
    driver_dfs.append(df)
    
# Stack Driver CSVs
driver_df = pd.concat(driver_dfs, ignore_index=True)

# Write to Drivers Race Snapshots in DB
driver_df.to_sql("drivers_race_snapshots", con, if_exists="replace", index=False)

# Same for Constructors
constructor_files = []

for file in processed_files:
    if file.startswith("constructors_race_"):
        constructor_files.append(file)
constructor_files.sort()
        
constructor_dfs = []

for file in constructor_files:
    filepath = os.path.join(PROCESSED_DIR, file) 
    df = pd.read_csv(filepath)
    constructor_dfs.append(df)
    
constructor_df = pd.concat(constructor_dfs, ignore_index=True)

constructor_df.to_sql("constructors_race_snapshots", con, if_exists="replace", index=False)

# Write Race Data file to DB
races_filepath = os.path.join("data", "reference", "races_2026.csv")

races_df = pd.read_csv(races_filepath)
races_df["race_date"] = pd.to_datetime(races_df["race_date"], utc=True)

races_df.to_sql("races", con, if_exists="replace", index=False)

# Close Connection
con.close()