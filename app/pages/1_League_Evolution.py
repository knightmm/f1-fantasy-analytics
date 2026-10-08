import streamlit as st
from config import API_URL
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go

st.title("League Evolution")

# Get team history from the API
response = requests.get(
    f"{API_URL}/teams/by-race",
    timeout=30,
)
response.raise_for_status()

# Convert JSON records into dataframe
df = pd.DataFrame(response.json())

# Metric selector
metrics = {
    "Cumulative points": "cumulative_points",
    "Total wealth": "total_wealth",
    "Asset value": "asset_value",
    "Remaining cash": "remaining_budget",
}

selected_metric = st.selectbox(
    "Metric",
    list(metrics),
)

metric_column = metrics[selected_metric]

# Identify each team using its owner and team number
df["team_key"] = (
    df["user_guid"].astype(str)
    + "_"
    + df["team_no"].astype(str)
)

# Line chart of team evolution across races
chart_df = df.sort_values("race_number")

fig = px.line(
    chart_df,
    x="race_number",
    y=metric_column,
    color="team_name",
    line_group="team_key",
    markers=True,
    labels={
        "race_number": "Race",
        metric_column: selected_metric,
        "team_name": "Team",
    },
)

fig.update_xaxes(dtick=1)

# Match the selected metric to its league average
average_columns = {
    "Cumulative points": "league_average_cumulative_points",
    "Total wealth": "league_average_total_wealth",
}

average_column = average_columns.get(selected_metric)

if average_column is not None:
    # The same average appears on every team's row; keep one per race
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
                color="black",
                dash="dash",
                width=3,
            ),
        )
    )
    
    fig.update_traces(
    opacity=0.8,
    line=dict(width=1.5),
    )


st.plotly_chart(fig, use_container_width=True)

st.subheader("Race details")

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

# Keep the selected race's team records
race_df = df[df["race_number"] == selected_race].copy()

display_df = (
    race_df.sort_values("cumulative_points", ascending=False)[
        [
            "team_name",
            "race_points",
            "race_rank",
            "cumulative_points",
            "asset_value",
            "remaining_budget",
            "total_wealth",
            "wealth_change",
        ]
    ]
    .rename(
        columns={
            "team_name": "Team",
            "race_points": "Race points",
            "race_rank": "Race rank",
            "cumulative_points": "Cumulative points",
            "asset_value": "Asset value ($m)",
            "remaining_budget": "Cash ($m)",
            "total_wealth": "Total wealth ($m)",
            "wealth_change": "Wealth change ($m)",
        }
    )
)

st.dataframe(
    display_df,
    hide_index=True,
    use_container_width=True,
)