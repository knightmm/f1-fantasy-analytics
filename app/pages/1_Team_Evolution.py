import streamlit as st
from config import API_URL, DEFAULT_TEAM
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go

st.title("📈 Team Evolution")

# Get team history for the selected season
response = requests.get(
    f"{API_URL}/teams/by-race",
    params={"season": 2026},
    timeout=30,
)
response.raise_for_status()

df = pd.DataFrame(response.json())

if df.empty:
    st.info("No team history is available for this season.")
    st.stop()

latest_race = int(df["race_number"].max())

# Stable identifier for each team
df["team_key"] = (
    df["user_guid"].astype(str)
    + "_"
    + df["team_no"].astype(str)
)

# Latest championship order, followed by teams absent from that snapshot
team_lookup = (
    df.sort_values("race_number")
    .drop_duplicates("team_key", keep="last")
    .copy()
)

team_lookup["in_latest_snapshot"] = (
    team_lookup["race_number"] == latest_race
)

team_lookup = team_lookup.sort_values(
    ["in_latest_snapshot", "cumulative_points", "team_name"],
    ascending=[False, False, True],
)

team_options = team_lookup["team_key"].tolist()
team_labels = team_lookup.set_index("team_key")["team_name"].to_dict()

default_matches = team_lookup.loc[
    team_lookup["team_name"] == DEFAULT_TEAM,
    "team_key",
].tolist()

default_index = (
    team_options.index(default_matches[0])
    if default_matches
    else 0
)

# 1 - SEASON EVOLUTION
st.subheader("Season Evolution")
st.markdown("**Who’s pulling ahead in points and team value?**")

metrics = {
    "Season points": "cumulative_points",
    "Total value": "total_wealth",
    "Asset value": "asset_value",
    "Cash": "remaining_budget",
}

team_col, metric_col = st.columns(2)

with team_col:
    selected_team_key = st.selectbox(
        "Your team",
        options=team_options,
        index=default_index,
        format_func=lambda team: team_labels[team],
    )

with metric_col:
    selected_metric = st.selectbox(
        "Metric",
        options=list(metrics),
    )

metric_column = metrics[selected_metric]

show_all = st.toggle("Show all teams", value=False)

if show_all:
    teams_to_plot = team_options
else:
    other_teams = st.multiselect(
        "Add teams to compare",
        options=[
            team for team in team_options
            if team != selected_team_key
        ],
        format_func=lambda team: team_labels[team],
        help="Teams are listed in the latest championship order.",
    )

    # Preserve championship order in the chart legend
    teams_to_plot = [
        team for team in team_options
        if team == selected_team_key or team in other_teams
    ]

chart_df = (
    df.loc[df["team_key"].isin(teams_to_plot)]
    .sort_values(["team_key", "race_number"])
    .copy()
)

chart_df["chart_team_name"] = chart_df["team_key"].map(team_labels)

# Keep team colours consistent when changing the selection
palette = [
    "#2A9D8F", "#E9B44C", "#7B6DCC", "#E07865", "#4C91C7",
    "#B56B9B", "#78964A", "#C58B50", "#526CA6", "#A45B62",
    "#508F87", "#8F78A8", "#92934E", "#B57650", "#667C89",
]

colour_map = {
    team: palette[index % len(palette)]
    for index, team in enumerate(team_options)
}

y_label = (
    "Season points"
    if selected_metric == "Season points"
    else f"{selected_metric} ($m)"
)

fig = px.line(
    chart_df,
    x="race_number",
    y=metric_column,
    color="team_key",
    line_group="team_key",
    markers=True,
    color_discrete_map=colour_map,
    category_orders={"team_key": team_options},
    custom_data=["chart_team_name"],
    labels={
        "race_number": "Race",
        metric_column: y_label,
        "team_key": "Team",
    },
)

number_format = ".0f" if selected_metric == "Season points" else ".1f"

for trace in fig.data:
    team_key = trace.name
    trace.name = team_labels[team_key]

    # Make the main team easier to follow
    trace.line.width = 4 if team_key == selected_team_key else 2
    trace.marker.size = 7 if team_key == selected_team_key else 5

fig.update_traces(
    hovertemplate=(
        "<b>%{customdata[0]}</b>"
        "<br>Race %{x}"
        f"<br>{y_label}: %{{y:{number_format}}}"
        "<extra></extra>"
    ),
)

# Keep the whole-league benchmark for points and total value
average_columns = {
    "Season points": "league_average_cumulative_points",
    "Total value": "league_average_total_wealth",
}

average_column = average_columns.get(selected_metric)

if average_column is not None:
    averages = (
        df[["race_number", average_column]]
        .drop_duplicates("race_number")
        .sort_values("race_number")
    )

    fig.add_trace(
        go.Scatter(
            x=averages["race_number"],
            y=averages[average_column],
            mode="lines",
            name="League average",
            line=dict(
                color="#888888",
                dash="dash",
                width=2,
            ),
            hovertemplate=(
                "<b>League average</b>"
                "<br>Race %{x}"
                f"<br>{y_label}: %{{y:{number_format}}}"
                "<extra></extra>"
            ),
        )
    )

fig.update_layout(
    height=520,
    margin=dict(l=10, r=10, t=15, b=10),
    legend=dict(
        title=None,
        orientation="h",
        yanchor="top",
        y=-0.18,
        xanchor="left",
        x=0,
    ),
)

fig.update_xaxes(
    dtick=1,
    title="Race",
    showgrid=False,
)

fig.update_yaxes(
    title=y_label,
    tickformat=number_format,
    gridcolor="rgba(128, 128, 128, 0.15)",
)

st.plotly_chart(fig, use_container_width=True)

# 2 - RACE PERFORMANCE AND VALUE
st.subheader("Race Performance & Value")
st.markdown("**How did teams score—and how did their value change?**")

# One entry per race for the selector
race_lookup = (
    df[["race_number", "race_name"]]
    .drop_duplicates()
    .sort_values("race_number")
)

race_labels = dict(
    zip(race_lookup["race_number"], race_lookup["race_name"])
)

selected_race = st.selectbox(
    "Select race",
    race_lookup["race_number"].tolist(),
    index=len(race_lookup) - 1,
    format_func=lambda race: f"Race {race} — {race_labels[race]}",
)

# Keep all teams from this race, regardless of chart selections
race_df = df.loc[df["race_number"] == selected_race].copy()

race_df = race_df.sort_values(
    ["race_points", "wealth_change"],
    ascending=[False, False],
    na_position="last",
)

# Keep the selected team's identity for row highlighting
selected_rows = race_df["team_key"].eq(selected_team_key).tolist()

display_df = (
    race_df[
        [
            "team_name",
            "race_points",
            "wealth_change",
            "total_wealth",
        ]
    ]
    .rename(
        columns={
            "team_name": "Team",
            "race_points": "Race points",
            "wealth_change": "Value change ($m)",
            "total_wealth": "Total value ($m)",
        }
    )
    .reset_index(drop=True)
)


def highlight_selected_team(row):
    if selected_rows[row.name]:
        return ["background-color: rgba(233, 180, 76, 0.15);"] * len(row)
    return [""] * len(row)


def colour_value_change(value):
    if pd.isna(value):
        return ""
    if value > 0:
        return "color: #2E9D65; font-weight: bold;"
    if value < 0:
        return "color: #D97070; font-weight: bold;"
    return "font-weight: bold;"


styled_display = (
    display_df.style
    .apply(highlight_selected_team, axis=1)
    .map(
        colour_value_change,
        subset=["Value change ($m)"],
    )
)

st.dataframe(
    styled_display,
    hide_index=True,
    use_container_width=True,
    height=35 * (len(display_df) + 1) + 3,
    column_config={
        "Team": st.column_config.TextColumn(
            "Team",
            pinned=True,
        ),
        "Race points": st.column_config.NumberColumn(
            "Race points",
            format="%.0f",
        ),
        "Value change ($m)": st.column_config.NumberColumn(
            "Value change ($m)",
            format="%+.1f",
            help=(
                "Change in total team value since the team's "
                "previous available race snapshot."
            ),
        ),
        "Total value ($m)": st.column_config.NumberColumn(
            "Total value ($m)",
            format="%.1f",
            help="Asset value plus remaining cash.",
        ),
    },
)

st.caption(
    "Value change compares total team value with the previous "
    "available race snapshot."
)

st.caption(f"Data through race {latest_race}.")