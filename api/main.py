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


@app.get(
    "/",
    summary="Check API status",
    description="""
Confirms that the API is running.
Does not check database availability or data freshness.
""",
)
def root():
    return {"message": "F1 Fantasy API running"}


@app.get(
    "/assets/latest",
    summary="Get latest asset prices and points",
    description="""
Returns one row per driver or constructor with current prices,
price changes, points and selection percentages.

Filters: asset_type and display_name.
Prices and points may refer to different race snapshots.
""",
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
Returns one row per asset per race with prices, price changes,
points and selection percentages.

Filters: asset_type, display_name and race_number.
Results are ordered by largest value change; limit defaults to 20.
""",
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

    if race_number is not None:
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
    "/team/assets/latest",
    summary="Get latest team assets",
    description="""
Returns one row per roster asset entry in the latest loaded
team snapshot, enriched with asset prices and points.

Filters: team_name.
Asset prices and points may refer to a different race from the lineup.
""",
)
def get_latest_team_assets(
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
    "/teams/by-race",
    summary="Get team performance and finances by race",
    description="""
Returns one row per team per race with official points,
cumulative points, finances, wealth changes and league averages.

Filters: season, race_number and team_name.
Recorded valuations are preferred, with calculated fallbacks where possible.
""",
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
Returns one row per team present at the latest loaded race
of each season, with points, championship rank and finances.

Filters: season and team_name.
League ranks are calculated before filtering; absent teams are excluded.
""",
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


@app.get(
    "/teams/chips",
    summary="Get team chip usage and status",
    description="""
Returns one row per team per chip with status, activation race,
team race points and the corresponding league average.

Filters: season, team_name, chip_id and chip_status.
Status uses each team's latest snapshot; scores do not measure chip impact.
""",
)
def get_team_chips(
    season: int | None = None,
    team_name: str | None = None,
    chip_id: int | None = None,
    chip_status: str | None = None,
):
    query = """
        SELECT
            season,
            user_guid,
            team_no,
            team_name,
            last_observed_race,
            chip_id,
            chip_name,
            chip_short_name,
            available_first_race,
            race_used,
            race_used_name,
            race_used_short_name,
            chip_status,
            chip_race_points,
            league_average_race_points
        FROM mart_team_chips
    """

    params = []
    filters = []

    if season is not None:
        filters.append("season = ?")
        params.append(season)

    if team_name:
        filters.append("LOWER(team_name) LIKE LOWER(?)")
        params.append(f"%{team_name}%")

    if chip_id is not None:
        filters.append("chip_id = ?")
        params.append(chip_id)

    if chip_status:
        filters.append("chip_status = ?")
        params.append(chip_status.lower())

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += """
        ORDER BY
            season,
            team_name,
            user_guid,
            team_no,
            chip_id
    """

    return run_query(query, params)