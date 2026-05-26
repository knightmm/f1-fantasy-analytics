-- Driver Value Changes by Race
DROP TABLE IF EXISTS mart_driver_value_changes;

CREATE TABLE mart_driver_value_changes AS
SELECT 
    season,
    race_number,
    asset_id,
    display_name,
    value,
    old_asset_value,
    ROUND(value - old_asset_value, 2) AS value_change,
    gameday_points,
    overall_points,
    selected_percentage

FROM drivers_race_snapshots;

-- Constructor Value Changes by Race
DROP TABLE IF EXISTS mart_constructor_value_changes;

CREATE TABLE mart_constructor_value_changes AS
SELECT 
    season,
    race_number,
    asset_id,
    display_name,
    value,
    old_asset_value,
    ROUND(value - old_asset_value, 2) AS value_change,
    gameday_points,
    overall_points,
    selected_percentage
FROM constructors_race_snapshots;


-- Driver Season Summary
DROP TABLE IF EXISTS mart_driver_season_value_summary;

CREATE TABLE mart_driver_season_value_summary AS
SELECT
    asset_id,
    display_name,
    ROUND(SUM(value_change), 2) AS total_value_change,
    MAX(overall_points) AS current_overall_points
FROM mart_driver_value_changes
GROUP BY asset_id, display_name;

-- Constructor Season Summary
DROP TABLE IF EXISTS mart_constructor_season_value_summary;

CREATE TABLE mart_constructor_season_value_summary AS
SELECT
    asset_id,
    display_name,
    ROUND(SUM(value_change), 2) AS total_value_change,
    MAX(overall_points) AS current_overall_points
FROM mart_constructor_value_changes
GROUP BY asset_id, display_name;

-- Driver and Constructor Value Snapshots
DROP TABLE IF EXISTS mart_asset_snapshots;

CREATE TABLE mart_asset_snapshots AS

SELECT
    race_number,
    asset_id,
    'driver' AS asset_type,
    display_name,
    value,
    overall_points
FROM drivers_race_snapshots

UNION ALL

SELECT
    race_number,
    asset_id,
    'constructor' AS asset_type,
    display_name,
    value,
    overall_points
FROM constructors_race_snapshots;

-- Assets and Prices from Latest Race Only
DROP TABLE IF EXISTS mart_assets_latest;

CREATE TABLE mart_assets_latest AS

SELECT 
	*
FROM mart_asset_snapshots
WHERE race_number = (
	SELECT MAX(race_number)
	FROM mart_asset_snapshots
);

-- Current official asset prices from latest price feed
DROP TABLE IF EXISTS mart_asset_latest_prices;

CREATE TABLE mart_asset_latest_prices AS

SELECT
    season,
    price_feed_race_number,
    price_feed_race_number - 1 AS race_causing_change,
    asset_id,
    asset_type,
    display_name,
    current_value,
    previous_value,
    ROUND(current_value - previous_value, 1) AS latest_value_change,
    retrieved_at_utc,
    feed_time_utc
FROM asset_price_snapshots
WHERE price_feed_race_number = (
    SELECT MAX(price_feed_race_number)
    FROM asset_price_snapshots
);