import streamlit as st
from config import API_URL, DEFAULT_TEAM
import pandas as pd
import requests
import plotly.express as px
import os

st.title("🏁 F1 Fantasy Dashboard")

st.write(
    "This dashboard makes it easier to compare performance and finances across your F1 Fantasy league. It brings standings, team wealth and remaining cash into one view, helping you see how your team compares with your league rivals."
)

# Latest team performance and finances
response = requests.get(
    f"{API_URL}/teams/latest",
    params={"season": 2026},
    timeout=30,
)
response.raise_for_status()

df = pd.DataFrame(response.json())

if df.empty:
    st.info("No team data is available for this season.")
    st.stop()

# Rank teams by official points in the latest race
df["league_race_rank"] = (
    df["race_points"]
    .rank(method="min", ascending=False)
    .astype(int)
)

# Identify the snapshot displayed on this page
latest_race = df.iloc[0]

DEFAULT_TEAM = os.getenv("DEFAULT_TEAM", "")

team_options = sorted(df["team_name"].tolist())

default_index = (
    team_options.index(DEFAULT_TEAM)
    if DEFAULT_TEAM in team_options
    else 0
)

selected_team = st.selectbox(
    "Select team",
    team_options,
    index=default_index,
)

my_row = df[df["team_name"] == selected_team].iloc[0]

# Load history to compare with the previous league race
history_response = requests.get(
    f"{API_URL}/teams/by-race",
    params={"season": 2026},
    timeout=30,
)
history_response.raise_for_status()

history_df = pd.DataFrame(history_response.json())

season_rank_change = None
race_rank_change = None

current_race = int(my_row["race_number"])

if not history_df.empty:
    earlier_races = history_df.loc[
        history_df["race_number"] < current_race,
        "race_number",
    ]

    if not earlier_races.empty:
        previous_race = int(earlier_races.max())

        previous_df = history_df.loc[
            history_df["race_number"] == previous_race
        ].copy()

        # Rank all teams before finding the selected team
        previous_df["season_league_rank"] = (
            previous_df["cumulative_points"]
            .rank(method="min", ascending=False)
        )

        previous_df["league_race_rank"] = (
            previous_df["race_points"]
            .rank(method="min", ascending=False)
        )

        previous_team = previous_df.loc[
            (previous_df["user_guid"] == my_row["user_guid"])
            & (previous_df["team_no"] == my_row["team_no"])
        ]

        if not previous_team.empty:
            previous_row = previous_team.iloc[0]

            season_rank_change = (
                int(previous_row["season_league_rank"])
                - int(my_row["league_rank"])
            )

            race_rank_change = (
                int(previous_row["league_race_rank"])
                - int(my_row["league_race_rank"])
            )


def rank_delta(change):
    if change is None or change == 0:
        return None

    unit = "place" if abs(change) == 1 else "places"
    return f"{change:+d} {unit}"

# 1 - TEAM OVERVIEW
# Performance metrics
st.subheader(f"{selected_team} Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.container(border=True):
        st.metric(
            "Season league rank",
            int(my_row["league_rank"]),
            delta=rank_delta(season_rank_change),
        )

        if season_rank_change == 0:
            st.caption("Unchanged")
        elif season_rank_change is None:
            st.caption("No previous race comparison")

with col2:
    with st.container(border=True):
        st.metric(
            "Season points",
            int(my_row["cumulative_points"]),
        )

with col3:
    with st.container(border=True):
        st.metric(
            "Latest race rank",
            int(my_row["league_race_rank"]),
            delta=rank_delta(race_rank_change),
        )

        if race_rank_change == 0:
            st.caption("Unchanged")
        elif race_rank_change is None:
            st.caption("No previous race comparison")

with col4:
    with st.container(border=True):
        st.metric(
            "Latest race points",
            int(my_row["race_points"]),
        )


# Financial metrics
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.metric(
            "Total value",
            f"${my_row['total_wealth']:.1f}m"
            if pd.notna(my_row["total_wealth"])
            else "Unavailable",
            delta=(
                f"{my_row['wealth_change']:+.1f}m"
                if pd.notna(my_row["wealth_change"])
                else None
            ),
        )

with col2:
    with st.container(border=True):
        st.metric(
            "Asset value",
            f"${my_row['asset_value']:.1f}m"
            if pd.notna(my_row["asset_value"])
            else "Unavailable",
        )

with col3:
    with st.container(border=True):
        st.metric(
            "Remaining cash",
            f"${my_row['remaining_budget']:.1f}m"
            if pd.notna(my_row["remaining_budget"])
            else "Unavailable",
        )

# All teams present in the latest race snapshot
chart_df = df.copy()

# One league snapshot combining standings and finances
display_df = (
    df.sort_values("league_rank")[
        [
            "league_rank",
            "team_name",
            "cumulative_points",
            "total_wealth",
            "wealth_change",          
            "asset_value",
            "remaining_budget",
            "race_points",
            "league_race_rank"
        ]
    ]
    .rename(
        columns={
            "league_rank": "Rank",
            "team_name": "Team",
            "cumulative_points": "Season points",
            "race_points": "Latest race points",
            "league_race_rank": "Latest race rank",
            "asset_value": "Asset value ($m)",
            "remaining_budget": "Cash ($m)",
            "total_wealth": "Total value ($m)",
            "wealth_change": "Value change ($m)",
        }
    )
)

# 2 - VALUE BAR CHART
# Stacked asset value and remaining cash
st.subheader("Team Finances")
st.markdown("**Whose team is the most valuable—and how much is held in cash?**")

finance_df = (
    chart_df
    .dropna(subset=["asset_value", "remaining_budget", "total_wealth"])
    .sort_values("total_wealth", ascending=True)
    .copy()
)

# Convert the two financial columns into rows for stacked bars
plot_df = finance_df.melt(
    id_vars=["team_name", "total_wealth", "wealth_change"],
    value_vars=["asset_value", "remaining_budget"],
    var_name="component",
    value_name="value",
)

# Highlight the selected team's asset portion
plot_df["segment"] = plot_df.apply(
    lambda row: (
        "Cash"
        if row["component"] == "remaining_budget"
        else (
            "Selected team's assets"
            if row["team_name"] == selected_team
            else "Assets"
        )
    ),
    axis=1,
)

fig = px.bar(
    plot_df,
    x="value",
    y="team_name",
    color="segment",
    orientation="h",
    barmode="stack",
    category_orders={
        "team_name": finance_df["team_name"].tolist(),
        "segment": ["Assets", "Selected team's assets", "Cash"],
    },
    color_discrete_map={
        "Assets": "#64B6AC",
        "Cash": "#9B8AC4",
        "Selected team's assets": "#E9B44C",
    },
    custom_data=["total_wealth", "wealth_change"],
    labels={
        "value": "Value ($m)",
        "team_name": "Team",
        "segment": "Component",
    },
)

# Set legend order independently of the bar stacking order
legend_order = {
    "Assets": 0,
    "Cash": 1,
    "Selected team's assets": 2,
}

for trace in fig.data:
    trace.legendrank = legend_order[trace.name]

    if trace.name == "Selected team's assets":
        trace.name = "Selected team"

fig.update_layout(
    height=max(350, 30 * len(finance_df) + 100),
    margin=dict(l=0, r=20, t=35, b=10),
    yaxis_title=None,
    legend_title_text="",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.04,
        xanchor="left",
        x=0,
        traceorder="normal",
    ),
    bargap=0.4,
    font=dict(size=12),
)

fig.update_xaxes(
    title_text="Value ($m)",
    rangemode="tozero",
    ticksuffix="m",
    showgrid=True,
    gridcolor="rgba(128, 128, 128, 0.15)",
    zeroline=False,
    showline=False,
)

fig.update_yaxes(
    categoryorder="array",
    categoryarray=finance_df["team_name"].tolist(),
    showgrid=False,
    ticks="",
    showline=False,
)

st.plotly_chart(fig, use_container_width=True)


# 3 - LEAGUE SNAPSHOT
st.subheader("Latest League Snapshot")
st.markdown("**How do teams compare on points and finances?**")

def highlight_selected_team(row):
    if row["Team"] == selected_team:
        return [
            "background-color: rgba(233, 180, 76, 0.18)"
        ] * len(row)

    return [""] * len(row)

styled_df = (
    display_df.style
    .apply(highlight_selected_team, axis=1)
    .format(
        {
            "Rank": "{:.0f}",
            "Season points": "{:.0f}",
            "Latest race points": "{:.0f}",
            "Latest race rank": "{:.0f}",
            "Asset value ($m)": "{:.1f}",
            "Cash ($m)": "{:.1f}",
            "Total value ($m)": "{:.1f}",
            "Value change ($m)": "{:.1f}",
        },
        na_rep="—",
    )
)

st.dataframe(
    styled_df,
    hide_index=True,
    height=35 * (min(len(display_df), 20) + 1) + 3,
    use_container_width=True,
    column_config={
        column: st.column_config.NumberColumn(
            column,
            format="%.1f",
        )
        for column in [
            "Asset value ($m)",
            "Cash ($m)",
            "Total value ($m)",
            "Value change ($m)",
        ]
    },
)

st.caption(
    "Financial values use recorded valuations where available, "
    "with calculated fallbacks for missing values. "
    )


st.caption(
    f"Data through race {latest_race['race_number']} "
    f"— {latest_race['race_name']}."
)