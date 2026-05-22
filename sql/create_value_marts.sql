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