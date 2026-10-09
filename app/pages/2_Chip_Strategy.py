import streamlit as st
from config import API_URL
import pandas as pd
import requests

st.title("🎯 Chip Strategy")

st.write(
    "Compare which chips each team has used "
    "and when they used them."
)

# Get all chips, including unused ones
response = requests.get(
    f"{API_URL}/teams/chips",
    params={"season": 2026},
    timeout=30,
)
response.raise_for_status()

df = pd.DataFrame(response.json())

if df.empty:
    st.info("No chip data is available for this season.")
    st.stop()

# Championship order toggle
championship_order = st.toggle(
    "Use championship order",
    value=True,
)

if championship_order:
    standings_response = requests.get(
        f"{API_URL}/teams/latest",
        params={"season": 2026},
        timeout=30,
    )
    standings_response.raise_for_status()

    standings_df = pd.DataFrame(standings_response.json())

    if not standings_df.empty:
        df = df.merge(
            standings_df[["user_guid", "team_no", "league_rank"]],
            on=["user_guid", "team_no"],
            how="left",
            validate="many_to_one",
        )
    else:
        df["league_rank"] = float("nan")

    team_order = (
        df[
            ["user_guid", "team_no", "team_name", "league_rank"]
        ]
        .drop_duplicates()
        .sort_values(
            ["league_rank", "team_name"],
            na_position="last",
        )
    )
else:
    team_order = (
        df[["user_guid", "team_no", "team_name"]]
        .drop_duplicates()
        .sort_values("team_name")
    )

# Numeric position used to order both tables
team_order["display_order"] = range(len(team_order))

# Latest observation across teams remains the reference snapshot
latest_race = int(df["last_observed_race"].max())

# Display text for each team/chip record
def make_chip_label(row):
    if row["chip_status"] == "unused":
        return "✕"

    location = row["race_used_short_name"]

    if pd.isna(location):
        return "Upcoming" if row["chip_status"] == "upcoming" else "Used"

    if row["chip_status"] == "upcoming":
        return f"Upcoming · {location}"

    return location


df["chip_label"] = df.apply(make_chip_label, axis=1)

# Keep the reference chip order
chip_order = (
    df[["chip_id", "chip_name"]]
    .drop_duplicates()
    .sort_values("chip_id")["chip_name"]
    .tolist()
)

# Turn chip records into one row per team
chip_table = df.pivot(
    index=[
        "user_guid",
        "team_no",
        "team_name",
        "last_observed_race",
    ],
    columns="chip_name",
    values="chip_label",
)

chip_table = (
    chip_table.reindex(columns=chip_order)
    .reset_index()
    .merge(
        team_order[["user_guid", "team_no", "display_order"]],
        on=["user_guid", "team_no"],
        how="left",
        validate="one_to_one",
    )
    .sort_values("display_order")
)

chip_table.columns.name = None

# Show only the team name and chip columns
display_df = chip_table[
    ["team_name"] + chip_order
].rename(
    columns={
        "team_name": "Team",
    }
)

# 1 - CHIP OVERVIEW
st.subheader("Chip Overview")
st.markdown("**Which chips have teams played—and what’s left?**")

def colour_chip_cell(value):
    if value == "✕":
        return "color: #D97070"
    return ""


styled_df = display_df.style.map(
    colour_chip_cell,
    subset=chip_order,
)

st.dataframe(
    styled_df,
    hide_index=True,
    use_container_width=True,
    height=35 * (min(len(display_df), 20) + 1) + 3,
)

st.caption(
    "✕ = no usage recorded · Locations show where the chip was used."
)

# 2- CHIP USAGE BY RACE
st.subheader("Chip Usage by Race")
st.markdown("**When did teams play their chips?**")

# Only completed, recorded chip activations
used_df = df[df["chip_status"] == "used"].copy()

# Include every observed team, even those with no chip usage
team_index = pd.MultiIndex.from_frame(
    team_order[["user_guid", "team_no", "team_name"]]
)

race_columns = list(range(1, latest_race + 1))

if used_df.empty:
    timing_df = pd.DataFrame(
        "",
        index=team_index,
        columns=race_columns,
    )
else:
    used_df["race_used"] = used_df["race_used"].astype(int)

    timing_df = used_df.pivot_table(
        index=["user_guid", "team_no", "team_name"],
        columns="race_used",
        values="chip_short_name",
        aggfunc=lambda chips: " / ".join(chips),
        fill_value="",
    )

    timing_df = timing_df.reindex(
        index=team_index,
        columns=race_columns,
        fill_value="",
    ).fillna("")

timing_df = timing_df.reset_index()

# Match each race number to its short name
race_names = (
    used_df[["race_used", "race_used_short_name"]]
    .dropna()
    .drop_duplicates()
    .set_index("race_used")["race_used_short_name"]
    .to_dict()
)

# Keep the team name and the races with recorded chip usage
timing_display = timing_df[
    ["team_name"] + race_columns
].rename(
    columns={
        "team_name": "Team",
        **{
            race: (
                f"R{race} · {race_names[race]}"
                if race in race_names
                else f"R{race}"
            )
            for race in race_columns
        },
    }
)

timing_display.columns.name = None

# Keep Team and only race columns containing at least one chip
columns_to_keep = [
    column
    for column in timing_display.columns
    if column == "Team"
    or timing_display[column]
    .fillna("")
    .astype(str)
    .str.strip()
    .ne("")
    .any()
]

timing_display = timing_display[columns_to_keep]

st.dataframe(
    timing_display,
    hide_index=True,
    use_container_width=True,
    height=35 * (min(len(timing_display), 20) + 1) + 3,
    column_config={
        "Team": st.column_config.TextColumn(
            "Team",
            pinned=True,
        ),
    },
)

st.caption(
    "Only races with recorded chip usage are shown. "
    "LL = Limitless · WC = Wildcard · FF = Final Fix · "
    "AP = Auto Pilot · NN = No Negative · X3 = x3 Boost."
)

# 3 - CHIP RACE PERFORMANCE
st.subheader("Chip Race Performance")
st.markdown("**Who scored the most above average when using a chip on a race?**")

st.caption(
    "Ranked by points above or below the league average "
    "in the race where each chip was used."
)

# Only completed chip activations with available scores
performance_df = df.loc[
    df["chip_status"] == "used"
].dropna(
    subset=["chip_race_points", "league_average_race_points"]
).copy()

if performance_df.empty:
    st.info("No chip race scores are available yet.")
else:
    performance_df["points_vs_average"] = (
        performance_df["chip_race_points"]
        - performance_df["league_average_race_points"]
    )

    performance_df = performance_df.sort_values(
        "points_vs_average",
        ascending=False,
    )

    performance_display = (
        performance_df[
            [
                "team_name",
                "points_vs_average",
                "chip_name",
                "race_used_short_name",
                "chip_race_points",
                "league_average_race_points",
            ]
        ]
        .rename(
            columns={
                "team_name": "Team",
                "points_vs_average": "vs average",
                "chip_name": "Chip",
                "race_used_short_name": "Race",
                "chip_race_points": "Race points",
                "league_average_race_points": "Race average",
            }
        )
        .reset_index(drop=True)
    )

    def colour_points_difference(value):
        if value > 0:
            return "color: #2E9D65; font-weight: bold;"
        if value < 0:
            return "color: #D97070; font-weight: bold;"
        return "font-weight: bold;"

    styled_performance = (
        performance_display.style
        .map(
            colour_points_difference,
            subset=["vs average"],
        )
        .format(
            {
                "vs average": "{:+.0f}",
                "Race points": "{:.0f}",
                "Race average": "{:.0f}",
            }
        )
    )

    st.dataframe(
        styled_performance,
        hide_index=True,
        use_container_width=True,
        height=35 * (min(len(performance_display), 20) + 1) + 3,
        column_config={
            "vs average": st.column_config.NumberColumn(
                "vs average",
                help="Team race points minus the league average for that race.",
                width="small",
            ),
            "Race average": st.column_config.NumberColumn(
                "Race average",
                format="%.0f",
            ),
        },
    )
    
st.caption(f"Data through race {latest_race}.")