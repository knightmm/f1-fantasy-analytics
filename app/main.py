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


@app.get("/assets/season-value-changes")
def get_asset_season_value_changes(
    asset_type: str | None = None,
    limit: int = 20,
):
    query = """
        SELECT
            asset_id,
            asset_type,
            display_name,
            total_value_change,
            current_overall_points
        FROM mart_asset_season_value_summary
    """

    params = []

    if asset_type:
        query += " WHERE asset_type = ?"
        params.append(asset_type.upper())

    query += """
        ORDER BY total_value_change DESC
        LIMIT ?
    """
    params.append(limit)

    return run_query(query, params)


@app.get("/assets/latest")
def get_latest_assets(
    asset_type: str | None = None,
    display_name: str | None = None,
):
    query = """ 
        SELECT
            race_number,
            asset_id,
            asset_type,
            display_name,
            value,
            old_asset_value,
            ROUND(value - old_asset_value, 1) AS latest_value_change,
            overall_points
        FROM mart_assets_latest
    """

    params = []
    filters = []

    if asset_type:
        filters.append("asset_type = ?")
        params.append(asset_type.upper())

    if display_name:
        filters.append("LOWER(display_name) LIKE LOWER(?)")
        params.append(f"%{display_name}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY asset_type, value DESC"

    return run_query(query, params)


@app.get("/assets/latest-prices")
def get_latest_asset_prices(
    asset_type: str | None = None,
    display_name: str | None = None,
):
    query = """
        SELECT
            price_feed_race_number,
            race_causing_change,
            asset_id,
            asset_type,
            display_name,
            current_value,
            previous_value,
            latest_value_change
        FROM mart_asset_latest_prices
    """

    params = []
    filters = []

    if asset_type:
        filters.append("asset_type = ?")
        params.append(asset_type.upper())

    if display_name:
        filters.append("LOWER(display_name) LIKE LOWER(?)")
        params.append(f"%{display_name}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY current_value DESC"

    return run_query(query, params)


@app.get("/league/team-values/latest")
def get_latest_league_team_values():
    query = """
        SELECT
            team_snapshot_race_number,
            price_feed_race_number,
            team_no,
            team_name,
            user_name,
            current_team_value,
            total_team_value_change,
            asset_count,
            likely_limitless_team
        FROM mart_league_team_values_latest
        ORDER BY current_team_value DESC
    """

    return run_query(query)