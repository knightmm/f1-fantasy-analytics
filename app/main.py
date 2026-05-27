from fastapi import FastAPI
import sqlite3
import pandas as pd
import os

app = FastAPI()

DB_PATH = os.path.join("data", "f1_fantasy.db")


def run_query(query, params=None):
    if params is None:
        params = []

    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(query, con, params=params)

    return df.to_dict(orient="records")


@app.get("/")
def root():
    return {"message": "F1 Fantasy API running"}


@app.get(
    "/assets/latest",
    summary="Get latest asset prices and points",
    description="""
    Returns the latest available asset data for all drivers and constructors.

    Combines:
    - latest official asset prices and value changes from the current feed
    - latest completed race points and selection statistics

    Supports filtering by:
    - asset_type
    - display_name
    """
)
def get_latest_assets(
    asset_type: str | None = None,
    display_name: str | None = None,
):
    query = """ 
        SELECT
            asset_id,
            asset_type,
            display_name,
            points_race_number,
            price_feed_race_number,
            race_causing_change,
            current_value,
            previous_value,
            latest_value_change,
            overall_points,
            gameday_points,
            selected_percentage
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

    query += " ORDER BY asset_type, current_value DESC"

    return run_query(query, params)


@app.get(
    "/assets/value-changes",
    summary="Get historical asset value changes",
    description="""
    Returns historical asset value changes by race for all drivers and constructors.

    Includes:
    - asset prices
    - value changes
    - race-by-race fantasy points
    - selection percentages

    Supports filtering by:
    - asset_type
    - display_name
    - race_number
    """
)
def get_asset_value_changes(
    asset_type: str | None = None,
    display_name: str | None = None,
    race_number: int | None = None,
):
    query = """
        SELECT
            season,
            race_number,
            asset_id,
            asset_type,
            display_name,
            value,
            old_asset_value,
            value_change,
            gameday_points,
            overall_points,
            selected_percentage
        FROM mart_asset_value_changes_by_race
    """

    params = []
    filters = []

    if asset_type:
        filters.append("asset_type = ?")
        params.append(asset_type.upper())

    if display_name:
        filters.append("LOWER(display_name) LIKE LOWER(?)")
        params.append(f"%{display_name}%")

    if race_number:
        filters.append("race_number = ?")
        params.append(race_number)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += """
        ORDER BY
            race_number,
            asset_type,
            display_name
    """

    return run_query(query, params)


@app.get(
    "/league/team-values/latest",
    summary="Get latest league team values",
    description="""
    Returns the latest estimated values of teams in the private F1 Fantasy league
    using the most recent asset prices.

    Grain:
    - one row per team

    Includes:
    - current team value
    - latest total team value change
    - latest completed race points
    - asset count
    - team owner information
    - likely limitless chip usage detection
    """
)
def get_latest_league_team_values(
    team_name: str | None = None,
    user_name: str | None = None,
):
    query = """
        SELECT
            team_snapshot_race_number,
            price_feed_race_number,
            team_name,
            user_name,
            current_team_value,
            total_team_value_change,
            latest_completed_team_points,
            asset_count,
            likely_limitless_team
        FROM mart_team_values_latest
    """

    params = []
    filters = []

    if team_name:
        filters.append("LOWER(team_name) LIKE LOWER(?)")
        params.append(f"%{team_name}%")

    if user_name:
        filters.append("LOWER(user_name) LIKE LOWER(?)")
        params.append(f"%{user_name}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY current_team_value DESC"

    return run_query(query, params)


@app.get(
    "/league/team-assets/latest",
    summary="Get latest league team assets"
    description="""
    Returns the latest known lineups for teams in the private F1 Fantasy league.

    Grain:
    - one row per asset in each team's latest lineup

    Includes:
    - team and user information
    - asset names and types
    - current asset values
    - latest value changes
    - latest completed race points
    """
)
def get_latest_league_team_assets(
    team_name: str | None = None,
    user_name: str | None = None,
):
    query = """
        SELECT
            team_snapshot_race_number,
            price_feed_race_number,
            points_race_number,
            team_name,
            user_name,
            asset_id,
            asset_type,
            display_name,
            current_value,
            latest_value_change,
            overall_points,
            latest_completed_race_points
        FROM mart_team_assets_latest
    """

    params = []
    filters = []

    if team_name:
        filters.append("LOWER(team_name) LIKE LOWER(?)")
        params.append(f"%{team_name}%")

    if user_name:
        filters.append("LOWER(user_name) LIKE LOWER(?)")
        params.append(f"%{user_name}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += """
        ORDER BY
            team_name,
            asset_type,
            current_value DESC
    """

    return run_query(query, params)