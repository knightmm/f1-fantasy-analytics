from fastapi import FastAPI
import sqlite3
import pandas as pd
import os

app = FastAPI()

DB_PATH = os.path.join("data", "f1_fantasy.db")


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

    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(query, con, params=(limit,))

    return df.to_dict(orient="records")

@app.get("/constructors/season-value-changes")
def get_constructor_season_value_changes(limit: int = 10):

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

    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(query, con, params=(limit,))

    return df.to_dict(orient="records")