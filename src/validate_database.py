import pandas as pd


def validate_database(con):
    # 1. Required tables, unique keys and populated key values
    keys = {
        "asset_race": ["season", "race_number", "asset_id"],
        "team_race": ["season", "race_number", "user_guid", "team_no"],
        "team_race_asset": [
            "season", "race_number", "user_guid", "team_no", "asset_id"
        ],
        "team_chip_usage": ["season", "user_guid", "team_no", "chip_id"],
        "races": ["season", "race_number"],
        "chips": ["chip_id"],
    }

    required_values = {
        "asset_race": ["asset_type", "value", "gameday_points"],
        "team_race": [
            "race_points", "race_rank", "remaining_budget",
            "transfers_made", "free_transfers_remaining"
        ],
        "team_race_asset": [
            "is_captain", "is_mg_captain", "player_position", "is_final"
        ],
        "team_chip_usage": ["race_used"],
    }

    tables = {}

    for table, key_columns in keys.items():
        exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()

        if not exists:
            raise ValueError(f"Missing table: {table}")

        df = pd.read_sql_query(f"SELECT * FROM {table}", con)
        tables[table] = df

        required_columns = key_columns + required_values.get(table, [])

        if table == "team_race":
            required_columns += [
                "recorded_asset_value", "recorded_total_budget"
            ]

        missing_columns = set(required_columns) - set(df.columns)

        if missing_columns:
            raise ValueError(
                f"{table}: missing columns {sorted(missing_columns)}"
            )

        # An empty chip usage table is valid if no chips have been used.
        if df.empty and table != "team_chip_usage":
            raise ValueError(f"{table}: table is empty")

        if df[key_columns].isna().any().any():
            raise ValueError(f"{table}: missing key values")

        if df.duplicated(subset=key_columns).any():
            raise ValueError(f"{table}: duplicate keys")

    # 2. Essential analytical values
    for table, columns in required_values.items():
        missing = tables[table][columns].isna().sum()
        missing = missing[missing > 0]

        if not missing.empty:
            raise ValueError(
                f"{table}: missing required values {missing.to_dict()}"
            )

    # Report optional valuation gaps without stopping the build.
    for column in ["recorded_asset_value", "recorded_total_budget"]:
        count = tables["team_race"][column].isna().sum()
        if count:
            print(f"Validation note: team_race.{column} missing in {count} rows")

    # 3. Relationships between tables
    # Each mapping lists (source column, related column).
    relationships = [
        (
            "team_race_asset", "team_race",
            [
                ("season", "season"),
                ("race_number", "race_number"),
                ("user_guid", "user_guid"),
                ("team_no", "team_no"),
            ],
        ),
        (
            "team_race_asset", "asset_race",
            [
                ("season", "season"),
                ("race_number", "race_number"),
                ("asset_id", "asset_id"),
            ],
        ),
        (
            "team_race", "races",
            [("season", "season"), ("race_number", "race_number")],
        ),
        (
            "asset_race", "races",
            [("season", "season"), ("race_number", "race_number")],
        ),
        (
            "team_chip_usage", "chips",
            [("chip_id", "chip_id")],
        ),
        (
            "team_chip_usage", "races",
            [("season", "season"), ("race_used", "race_number")],
        ),
        (
            "team_chip_usage", "team_race",
            [
                ("season", "season"),
                ("user_guid", "user_guid"),
                ("team_no", "team_no"),
            ],
        ),
    ]

    for source, related, columns in relationships:
        match = " AND ".join(
            f"s.{source_col} = r.{related_col}"
            for source_col, related_col in columns
        )

        query = f"""
            SELECT COUNT(*)
            FROM {source} s
            WHERE NOT EXISTS (
                SELECT 1 FROM {related} r
                WHERE {match}
            )
        """

        count = con.execute(query).fetchone()[0]

        if count:
            raise ValueError(
                f"{source} → {related}: {count} unmatched rows"
            )

    # Upcoming chip selections do not yet need race results.
    query = """
        SELECT COUNT(*)
        FROM team_chip_usage u
        WHERE u.race_used <= (
            SELECT MAX(t.race_number)
            FROM team_race t
            WHERE t.season = u.season
        )
        AND NOT EXISTS (
            SELECT 1 FROM team_race t
            WHERE t.season = u.season
              AND t.race_number = u.race_used
              AND t.user_guid = u.user_guid
              AND t.team_no = u.team_no
        )
    """

    count = con.execute(query).fetchone()[0]

    if count:
        raise ValueError(
            f"Historical chip usage: {count} unmatched team/race records"
        )

    print("Database validation passed.")