
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
FROM asset_race;


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
    FROM asset_race
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
    FROM asset_race a
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
    FROM asset_race a
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
    FROM team_race_asset
)

SELECT
    tas.season,
    tas.race_number AS team_snapshot_race_number,
    tas.user_guid,
    lss.team_no,
    lss.team_name,
    tas.asset_id,
    mal.asset_type,
    mal.display_name,
    mal.current_value,
    mal.latest_value_change,
    mal.overall_points,
    mal.gameday_points AS latest_completed_race_points,
    mal.points_race_number,
    mal.price_feed_race_number

FROM team_race_asset tas

JOIN latest_race lr
    ON tas.race_number = lr.race_number

LEFT JOIN team_race lss
    ON tas.season = lss.season
   AND tas.race_number = lss.race_number
   AND tas.user_guid = lss.user_guid
   AND tas.team_no = lss.team_no

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
    team_name

ORDER BY current_team_value DESC;


-- Team Values with Asset Prices and Performance per Race
DROP TABLE IF EXISTS mart_team_values_by_race;

CREATE TABLE mart_team_values_by_race AS
WITH team_asset_performance AS (

    SELECT
        tas.season,
        tas.race_number,
        tas.team_name,
        tas.team_no,
        tas.asset_id,
        avr.value,
        avr.value_change,
        avr.gameday_points
    FROM team_race_asset tas
    LEFT JOIN mart_asset_value_changes_by_race avr
        ON tas.season = avr.season
        AND tas.race_number = avr.race_number
        AND tas.asset_id = avr.asset_id

)

SELECT
    season,
    race_number,
    team_name,
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

-- Team performance and finances by race
DROP TABLE IF EXISTS mart_team_race;

CREATE TABLE mart_team_race AS
WITH roster_values AS (
    SELECT
        s.season,
        s.race_number,
        s.user_guid,
        s.team_no,

        -- Only calculate a value for a complete seven-asset roster.
        CASE
            WHEN COUNT(*) = 7 AND COUNT(a.value) = 7
                THEN ROUND(SUM(a.value), 1)
            ELSE NULL
        END AS calculated_asset_value

    FROM team_race_asset AS s
    LEFT JOIN asset_race AS a
        ON a.season = s.season
       AND a.race_number = s.race_number
       AND a.asset_id = s.asset_id

    -- Keep the original roster for Final Fix financial valuation.
    WHERE s.is_final != 1

      -- Limitless roster cost is not a valid wealth fallback.
      AND NOT EXISTS (
          SELECT 1
          FROM team_chip_usage AS u
          WHERE u.season = s.season
            AND u.user_guid = s.user_guid
            AND u.team_no = s.team_no
            AND u.race_used = s.race_number
            AND u.chip_id = 1
      )

    GROUP BY
        s.season,
        s.race_number,
        s.user_guid,
        s.team_no
),

team_metrics AS (
    SELECT
        t.season,
        t.race_number,
        r.race_name,
        t.user_guid,
        t.team_no,
        t.team_name,

        -- Official performance
        t.race_points,
        t.race_rank,

        SUM(t.race_points) OVER (
            PARTITION BY t.season, t.user_guid, t.team_no
            ORDER BY t.race_number
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_points,

        ROUND(
            AVG(t.race_points) OVER (
                PARTITION BY t.season, t.race_number
            ),
            2
        ) AS league_average_race_points,

        -- Preserve the source values for comparison.
        t.recorded_asset_value,
        t.remaining_budget,
        t.recorded_total_budget,
        v.calculated_asset_value,

        -- Prefer recorded values; use calculations when missing.
        COALESCE(
            t.recorded_asset_value,
            v.calculated_asset_value
        ) AS asset_value,

        ROUND(
            COALESCE(
                t.recorded_total_budget,
                COALESCE(
                    t.recorded_asset_value,
                    v.calculated_asset_value
                ) + t.remaining_budget
            ),
            1
        ) AS total_wealth,

        CASE
            WHEN t.recorded_asset_value IS NOT NULL THEN 'recorded'
            WHEN v.calculated_asset_value IS NOT NULL THEN 'calculated'
            ELSE 'unavailable'
        END AS valuation_source

    FROM team_race AS t
    JOIN races AS r
        ON t.season = r.season
       AND t.race_number = r.race_number

    LEFT JOIN roster_values AS v
        ON t.season = v.season
       AND t.race_number = v.race_number
       AND t.user_guid = v.user_guid
       AND t.team_no = v.team_no
)

SELECT
    m.*,

    -- Change from this team's previous available race snapshot.
    ROUND(
        m.total_wealth - LAG(m.total_wealth) OVER (
            PARTITION BY m.season, m.user_guid, m.team_no
            ORDER BY m.race_number
        ),
        1
    ) AS wealth_change,

    -- League averages at each race.
    ROUND(
        AVG(m.cumulative_points) OVER (
            PARTITION BY m.season, m.race_number
        ),
        2
    ) AS league_average_cumulative_points,

    ROUND(
        AVG(m.total_wealth) OVER (
            PARTITION BY m.season, m.race_number
        ),
        1
    ) AS league_average_total_wealth

FROM team_metrics AS m;