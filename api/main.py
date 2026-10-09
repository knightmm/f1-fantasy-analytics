from fastapi import FastAPI
import sqlite3
import pandas as pd
import os

app = FastAPI()

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DB_PATH = os.path.join(PROJECT_ROOT, "data", "f1_fantasy.db")

def run_query(query, params=None):
    if params is None:
        params = []

    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(query, con, params=params)

    # Return missing values as JSON null.
    df = df.astype(object).where(pd.notna(df), None)

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
    limit: int = 20,
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
            value_change DESC
        LIMIT ?
    """
    params.append(limit)

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
    - team information
    - likely limitless chip usage detection
    """
)
def get_latest_league_team_values(
    team_name: str | None = None,
):
    query = """
        SELECT
            team_snapshot_race_number,
            price_feed_race_number,
            team_name,
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

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY current_team_value DESC"

    return run_query(query, params)


@app.get(
    "/league/team-assets/latest",
    summary="Get latest league team assets",
    description="""
    Returns the latest known lineups for teams in the private F1 Fantasy league.

    Grain:
    - one row per asset in each team's latest lineup

    Includes:
    - team information
    - asset names and types
    - current asset values
    - latest value changes
    - latest completed race points
    """
)
def get_latest_league_team_assets(
    team_name: str | None = None,
):
    query = """
        SELECT
            team_snapshot_race_number,
            price_feed_race_number,
            points_race_number,
            team_name,
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

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += """
        ORDER BY
            team_name,
            asset_type,
            current_value DESC
    """

    return run_query(query, params)


@app.get(
    "/league/team-season-summary",
    summary="Get current team season summary",
    description="""
    Returns one row per team with season-to-date calculated points,
    latest team value, latest race points, and likely Limitless usage.

    Grain:
    - one row per team

    Notes:
    - points are calculated from asset points, not official league standings
    - Limitless usage is estimated from unusually high team value
    """
)
def get_team_season_summary(
    team_name: str | None = None,
):
    query = """
        SELECT
            season,
            latest_race_number,
            team_name,
            cumulative_calculated_points,
            latest_team_value,
            latest_team_value_change,
            latest_calculated_asset_points,
            has_used_limitless
        FROM mart_team_season_summary
    """

    params = []
    filters = []

    if team_name:
        filters.append("LOWER(team_name) LIKE LOWER(?)")
        params.append(f"%{team_name}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY cumulative_calculated_points DESC"

    return run_query(query, params)


@app.get(
    "/teams/by-race",
    summary="Get team performance and finances by race",
    description="""
        Returns one row per team per race, with official points, cumulative points, financial values and league averages."
    """
)
def get_teams_by_race(
    season: int | None = None,
    race_number: int | None = None,
    team_name: str | None = None,
):
    query = """
        SELECT
            t.season,
            t.race_number,
            t.race_name,
            r.race_date,
            r.sprint_weekend,
            t.user_guid,
            t.team_no,
            t.team_name,
            t.race_points,
            t.race_rank,
            t.cumulative_points,
            t.league_average_race_points,
            t.league_average_cumulative_points,
            t.asset_value,
            t.remaining_budget,
            t.total_wealth,
            t.wealth_change,
            t.league_average_total_wealth,
            t.valuation_source
        FROM mart_team_race AS t
        LEFT JOIN races AS r
            ON t.season = r.season
           AND t.race_number = r.race_number
    """

    params = []
    filters = []

    if season is not None:
        filters.append("t.season = ?")
        params.append(season)

    if race_number is not None:
        filters.append("t.race_number = ?")
        params.append(race_number)

    if team_name:
        filters.append("LOWER(t.team_name) LIKE LOWER(?)")
        params.append(f"%{team_name}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += """
        ORDER BY
            t.season,
            t.race_number,
            t.cumulative_points DESC,
            t.user_guid,
            t.team_no
    """

    return run_query(query, params)

@app.get(
    "/teams/latest",
    summary="Get latest team performance and finances",
    description="""
    Returns one row per team at the latest loaded race of each season, with official points, league position and corrected financial values.
    """
)
def get_latest_teams(
    season: int | None = None,
    team_name: str | None = None,
):
    query = """
        WITH latest_race AS (
            SELECT
                season,
                MAX(race_number) AS race_number
            FROM mart_team_race
            GROUP BY season
        ),

        latest_teams AS (
            SELECT
                t.*,

                RANK() OVER (
                    PARTITION BY t.season
                    ORDER BY t.cumulative_points DESC
                ) AS league_rank

            FROM mart_team_race AS t

            JOIN latest_race AS l
                ON t.season = l.season
               AND t.race_number = l.race_number
        )

        SELECT
            season,
            race_number,
            race_name,
            user_guid,
            team_no,
            team_name,
            race_points,
            race_rank,
            cumulative_points,
            league_rank,
            asset_value,
            remaining_budget,
            total_wealth,
            wealth_change,
            valuation_source

        FROM latest_teams
    """

    params = []
    filters = []

    if season is not None:
        filters.append("season = ?")
        params.append(season)

    if team_name:
        filters.append("LOWER(team_name) LIKE LOWER(?)")
        params.append(f"%{team_name}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += """
        ORDER BY
            season,
            league_rank,
            user_guid,
            team_no
    """

    return run_query(query, params)