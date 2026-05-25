import os
import pandas as pd
from datetime import date

def get_completed_race_numbers():
    races_csv = os.path.join("data", "reference", "races_2026.csv")
    races = pd.read_csv(races_csv)
    races["race_date"] = pd.to_datetime(races["race_date"]).dt.date
    
    today = date.today()
    completed_races = races[races["race_date"] < today]
    
    return completed_races["race_number"].sort_values().tolist()