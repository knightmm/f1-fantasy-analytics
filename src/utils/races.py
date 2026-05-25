from pathlib import Path
import pandas as pd
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def get_completed_race_numbers():
    races_csv = (PROJECT_ROOT / "data" / "reference" / "races_2026.csv")
    
    races = pd.read_csv(races_csv)
    
    races["race_date"] = pd.to_datetime(races["race_date"]).dt.date
    
    today = date.today()
    completed_races = races[races["race_date"] < today]
    
    return completed_races["race_number"].sort_values().tolist()