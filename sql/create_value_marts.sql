-- Asset Value Changes by Race
DROP TABLE IF EXISTS mart_asset_value_changes_by_race;

CREATE TABLE mart_asset_value_changes_by_race AS
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
FROM asset_race_snapshots;


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
    FROM asset_race_snapshots
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
    FROM asset_race_snapshots a
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
    FROM asset_race_snapshots a
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


-- Latest Team Assets with Asset Details
DROP TABLE IF EXISTS mart_team_assets_latest;

CREATE TABLE mart_team_assets_latest AS
WITH latest_race AS (
    SELECT MAX(race_number) AS race_number
    FROM team_asset_snapshots
)

SELECT
    tas.season,
    tas.race_number AS team_snapshot_race_number,
    tas.user_guid,
    lss.team_no,
    lss.team_name,
    lss.user_name,

    tas.asset_id,
    mal.asset_type,
    mal.display_name,
    mal.current_value,
    mal.latest_value_change,
    mal.overall_points,
    mal.gameday_points AS latest_completed_race_points,
    mal.points_race_number,
    mal.price_feed_race_number

FROM team_asset_snapshots tas

JOIN latest_race lr
    ON tas.race_number = lr.race_number

LEFT JOIN league_standings_snapshots lss
    ON tas.season = lss.season
   AND tas.race_number = lss.race_number
   AND tas.user_guid = lss.user_guid

LEFT JOIN mart_assets_latest mal
    ON tas.asset_id = mal.asset_id

ORDER BY
    lss.team_name,
    mal.asset_type,
    mal.current_value DESC;


-- Latest Team Values
DROP TABLE IF EXISTS mart_team_values_latest;

CREATE TABLE mart_team_values_latest AS
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

FROM mart_team_assets_latest

GROUP BY
    season,
    team_snapshot_race_number,
    price_feed_race_number,
    user_guid,
    team_no,
    team_name,
    user_name

ORDER BY current_team_value DESC;


-- Team Values with Asset Prices and Performance per Race
DROP TABLE IF EXISTS mart_team_values_by_race;

CREATE TABLE mart_team_values_by_race AS
WITH team_asset_performance AS (

    SELECT
        tas.season,
        tas.race_number,
        tas.team_name,
        tas.user_name,
        tas.team_no,
        tas.asset_id,
        avr.value,
        avr.value_change,
        avr.gameday_points
    FROM team_asset_snapshots tas
    LEFT JOIN mart_asset_value_changes_by_race avr
        ON tas.season = avr.season
        AND tas.race_number = avr.race_number
        AND tas.asset_id = avr.asset_id

)

SELECT
    season,
    race_number,
    team_name,
    user_name,
    team_no,
    ROUND(SUM(value), 1) AS team_value,
    ROUND(SUM(value_change), 1) AS team_value_change,
    SUM(gameday_points) AS calculated_asset_points,
    CASE
        WHEN ROUND(SUM(value), 1) > 130 THEN 1
        ELSE 0
    END AS likely_limitless_team
FROM team_asset_performance
GROUP BY
    season,
    race_number,
    team_name,
    user_name,
    team_no;


-- Season Team Performance
DROP TABLE IF EXISTS mart_team_season_summary;

CREATE TABLE mart_team_season_summary AS
WITH latest_race AS (
    SELECT
        season,
        MAX(race_number) AS latest_race_number
    FROM mart_team_values_by_race
    GROUP BY season
),

team_season_totals AS (
    SELECT
        season,
        team_name,
        MAX(user_name) AS user_name,
        MAX(team_no) AS team_no,
        SUM(calculated_asset_points) AS cumulative_calculated_points,
        MAX(likely_limitless_team) AS has_used_limitless
    FROM mart_team_values_by_race
    GROUP BY
        season,
        team_name
),

latest_team_values AS (
    SELECT
        tv.*
    FROM mart_team_values_by_race tv
    JOIN latest_race lr
        ON tv.season = lr.season
        AND tv.race_number = lr.latest_race_number
)

SELECT
    tst.season,
    ltv.race_number AS latest_race_number,
    tst.team_name,
    tst.user_name,
    tst.team_no,
    tst.cumulative_calculated_points,
    ltv.team_value AS latest_team_value,
    ltv.team_value_change AS latest_team_value_change,
    ltv.calculated_asset_points AS latest_calculated_asset_points,
    tst.has_used_limitless
FROM team_season_totals tst
LEFT JOIN latest_team_values ltv
    ON tst.season = ltv.season
    AND tst.team_name = ltv.team_name;