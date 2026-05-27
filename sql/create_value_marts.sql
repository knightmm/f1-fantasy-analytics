-- Asset Value Changes by Race
DROP TABLE IF EXISTS mart_asset_value_changes;

CREATE TABLE mart_asset_value_changes AS
SELECT 
    season,
    race_number,
    asset_id,
    asset_type,
    display_name,
    value,
    old_asset_value,
    ROUND(value - old_asset_value, 2) AS value_change,
    gameday_points,
    overall_points,
    selected_percentage,
    retrieved_at_utc,
    feed_time_utc
FROM assets_race_snapshots;


-- Latest Asset Points and Values
DROP TABLE IF EXISTS mart_assets_latest;

CREATE TABLE mart_assets_latest AS
WITH latest_completed AS (
    SELECT MAX(race_number) AS race_number
    FROM races
    WHERE DATE(race_date) < DATE('now')
),

latest_price_feed AS (
    SELECT MAX(race_number) AS race_number
    FROM assets_race_snapshots
),

latest_points AS (
    SELECT
        a.asset_id,
        a.asset_type,
        a.display_name,
        a.race_number AS points_race_number,
        a.overall_points,
        a.gameday_points,
        a.selected_percentage
    FROM assets_race_snapshots a
    JOIN latest_completed lc
        ON a.race_number = lc.race_number
),

latest_prices AS (
    SELECT
        a.asset_id,
        a.asset_type,
        a.display_name,
        a.race_number AS price_feed_race_number,
        a.race_number - 1 AS race_causing_change,
        a.value AS current_value,
        a.old_asset_value AS previous_value,
        ROUND(a.value - a.old_asset_value, 1) AS latest_value_change,
        a.retrieved_at_utc,
        a.feed_time_utc
    FROM assets_race_snapshots a
    JOIN latest_price_feed lpf
        ON a.race_number = lpf.race_number
)

SELECT
    p.asset_id,
    p.asset_type,
    p.display_name,
    pts.points_race_number,
    p.price_feed_race_number,
    p.race_causing_change,
    p.current_value,
    p.previous_value,
    p.latest_value_change,
    pts.overall_points,
    pts.gameday_points,
    pts.selected_percentage,
    p.retrieved_at_utc,
    p.feed_time_utc
FROM latest_prices p
LEFT JOIN latest_points pts
    ON p.asset_id = pts.asset_id
    AND p.asset_type = pts.asset_type;


-- Latest league lineups with asset details
DROP TABLE IF EXISTS mart_league_lineups_latest;

CREATE TABLE mart_league_lineups_latest AS
WITH latest_race AS (
    SELECT MAX(race_number) AS race_number
    FROM league_team_assets
)

SELECT
    lta.season,
    lta.race_number AS team_snapshot_race_number,
    lta.user_guid,
    ls.team_no,
    ls.team_name,
    ls.user_name,

    lta.asset_id,
    mal.asset_type,
    mal.display_name,
    mal.current_value,
    mal.latest_value_change,
    mal.overall_points,
    mal.gameday_points AS latest_completed_race_points,
    mal.points_race_number,
    mal.price_feed_race_number

FROM league_team_assets lta

JOIN latest_race lr
    ON lta.race_number = lr.race_number

LEFT JOIN league_standings ls
    ON lta.season = ls.season
   AND lta.race_number = ls.race_number
   AND lta.user_guid = ls.user_guid

LEFT JOIN mart_assets_latest mal
    ON lta.asset_id = mal.asset_id

ORDER BY
    ls.team_name,
    mal.asset_type,
    mal.current_value DESC;


-- Latest league team values
DROP TABLE IF EXISTS mart_league_team_values_latest;

CREATE TABLE mart_league_team_values_latest AS
SELECT
    season,
    team_snapshot_race_number,
    price_feed_race_number,
    user_guid,
    team_no,
    team_name,
    user_name,

    ROUND(SUM(current_value), 1) AS current_team_value,
    ROUND(SUM(latest_value_change), 1) AS total_team_value_change,
    ROUND(SUM(latest_completed_race_points), 1) AS latest_completed_team_points,
    COUNT(*) AS asset_count,

    CASE
        WHEN ROUND(SUM(current_value), 1) > 130 THEN 1
        ELSE 0
    END AS likely_limitless_team

FROM mart_league_lineups_latest

GROUP BY
    season,
    team_snapshot_race_number,
    price_feed_race_number,
    user_guid,
    team_no,
    team_name,
    user_name

ORDER BY current_team_value DESC;

