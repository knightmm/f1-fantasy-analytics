from fastapi import FastAPI
import sqlite3
import pandas as pd
import os

app = FastAPI()

DB_PATH = os.path.join("data", "f1_fantasy.db")


def run_query(query, params=None):
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(query, con, params=params)

    return df.to_dict(orient="records")

@app.get("/")
def root():
    return {"message": "F1 Fantasy API running"}


@app.get("/drivers/season-value-changes")
def get_driver_season_value_changes(limit: int = 20):

    query = """
        SELECT
            asset_id,
            display_name,
            total_value_change,
            current_overall_points
        FROM mart_driver_season_value_summary
        ORDER BY total_value_change DESC
        LIMIT ?
    """

    df = run_query(query, params=(limit,))

    return df.to_dict(orient="records")

@app.get("/constructors/season-value-changes")
def get_constructor_season_value_changes(limit: int = 11):

    query = """
        SELECT
            asset_id,
            display_name,
            total_value_change,
            current_overall_points
        FROM mart_constructor_season_value_summary
        ORDER BY total_value_change DESC
        LIMIT ?
    """

    df = run_query(query, params=(limit,))

    return df.to_dict(orient="records")

@app.get("/assets/latest")
def get_latest_assets(asset_type: str | None = None):
    query = """ 
        SELECT
            race_number,
            asset_id,
            asset_type,
            display_name,
            value,
            overall_points
        FROM mart_assets_latest
    """
    
    params = []
    
    if asset_type:
        query += "WHERE asset_type = ?"
        params.append(asset_type)
    
    query += "ORDER BY asset_type, value DESC"
    
    return run_query(query, params)