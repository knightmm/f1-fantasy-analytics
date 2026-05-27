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


-- Asset Season Summary
DROP TABLE IF EXISTS mart_asset_season_value_summary;

CREATE TABLE mart_asset_season_value_summary AS
SELECT
    asset_id,
    asset_type,
    display_name,
    ROUND(SUM(value_change), 2) AS total_value_change,
    MAX(overall_points) AS current_overall_points
FROM mart_asset_value_changes
GROUP BY
    asset_id,
    asset_type,
    display_name;


-- Latest Asset Snapshot
DROP TABLE IF EXISTS mart_assets_latest;

CREATE TABLE mart_assets_latest AS
SELECT 
    *
FROM assets_race_snapshots
WHERE race_number = (
    SELECT MAX(race_number)
    FROM assets_race_snapshots
);

-- Current official asset prices from latest price feed
DROP TABLE IF EXISTS mart_asset_latest_prices;

CREATE TABLE mart_asset_latest_prices AS
SELECT
    season,
    race_number AS price_feed_race_number,
    race_number - 1 AS race_causing_change,
    asset_id,
    asset_type,
    display_name,
    value AS current_value,
    old_asset_value AS previous_value,
    ROUND(value - old_asset_value, 1) AS latest_value_change,
    retrieved_at_utc,
    feed_time_utc
FROM assets_race_snapshots
WHERE race_number = (
    SELECT MAX(race_number)
    FROM assets_race_snapshots
);

-- Latest lineup of teams in league
DROP TABLE IF EXISTS mart_league_team_assets_latest;

CREATE TABLE mart_league_team_assets_latest AS

WITH latest_race AS (
    SELECT MAX(race_number) AS race_number
    FROM league_team_assets
)

SELECT
    lta.season,
    lta.race_number,
    lta.user_guid,
    ls.team_no,
    ls.team_name,
    ls.user_name,
    lta.asset_id
FROM league_team_assets lta

JOIN latest_race lr
    ON lta.race_number = lr.race_number

LEFT JOIN league_standings ls
    ON lta.season = ls.season
   AND lta.race_number = ls.race_number
   AND lta.user_guid = ls.user_guid;


-- Latest league lineups with latest prices
DROP TABLE IF EXISTS mart_league_team_values_latest;

CREATE TABLE mart_league_team_values_latest AS
SELECT
    mlta.season,
    mlta.race_number AS team_snapshot_race_number,
    malp.price_feed_race_number,
    mlta.user_guid,
    mlta.team_no,
    mlta.team_name,
    mlta.user_name,

    ROUND(SUM(malp.current_value), 1) AS current_team_value,

    ROUND(SUM(malp.latest_value_change), 1)
        AS total_team_value_change,

    COUNT(*) AS asset_count,

    CASE
        WHEN ROUND(SUM(malp.current_value), 1) > 130 THEN 1
        ELSE 0
    END AS likely_limitless_team

FROM mart_league_team_assets_latest mlta

LEFT JOIN mart_asset_latest_prices malp
    ON mlta.asset_id = malp.asset_id

GROUP BY
    mlta.season,
    mlta.race_number,
    malp.price_feed_race_number,
    mlta.user_guid,
    mlta.team_no,
    mlta.team_name,
    mlta.user_name

ORDER BY current_team_value DESC;

