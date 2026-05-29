import streamlit as st
from config import API_URL
import pandas as pd
import requests
import plotly.express as px

st.title("🏁 F1 Fantasy Dashboard")
st.header("Circle-K League - Race by Race")

response = requests.get(
    f"{API_URL}/league/team-values/by-race"
)

data = response.json()
df = pd.DataFrame(data)

race_lookup = (
    df[["race_number", "race_name", "race_date", "sprint_weekend"]]
    .drop_duplicates()
    .sort_values("race_number")
)

race_lookup["label"] = (
    "Race "
    + race_lookup["race_number"].astype(str)
    + " - "
    + race_lookup["race_name"]
)

selected_label = st.selectbox(
    "Select race",
    race_lookup["label"],
    index=len(race_lookup) - 1
)

selected_race = race_lookup.loc[
    race_lookup["label"] == selected_label,
    "race_number"
].values[0]

selected_race_row = race_lookup[
    race_lookup["label"] == selected_label
].iloc[0]

race_df = (
    df[df["race_number"] == selected_race]
    .reset_index(drop=True)
)

race_df.index += 1

race_date = pd.to_datetime(
    selected_race_row["race_date"]
).strftime("%d %B %Y")

race_info = race_date

if selected_race_row["sprint_weekend"] == 1:
    race_info += " • Sprint Weekend"

# Race Info
st.subheader(f"{selected_label} Team Values")
st.caption(race_info)

# Race Leaderboard Dataframe
display_df = race_df[
    [
        "team_name",
        "user_name",
        "team_value",
        "team_value_change",
        "calculated_asset_points",
        "likely_limitless_team",
    ]
].rename(
    columns={
        "team_name": "Team",
        "user_name": "Manager",
        "team_value": "Team Value ($m)",
        "team_value_change": "Value Change ($m)",
        "calculated_asset_points": "Race Points",
        "likely_limitless_team": "Likely Limitless",
    }
)

display_df["Likely Limitless"] = (
    display_df["Likely Limitless"]
    .map({1: "✅", 0: ""})
)

# Bar Charts - Value and Value Change
exclude_limitless = st.checkbox(
    "Exclude likely limitless teams",
    value=True
)

if exclude_limitless:
    chart_df = race_df[race_df["likely_limitless_team"] == 0]
else:
    chart_df = race_df

col1, col2 = st.columns(2)

with col1:
    st.subheader("Team Value Leaderboard")

    team_value_df = chart_df.sort_values(
        "team_value",
        ascending=True
    )

    fig_value = px.bar(
        team_value_df,
        x="team_value",
        y="team_name",
        orientation="h",
        text="team_value",
        hover_data=[
            "user_name",
            "team_value_change",
            "calculated_asset_points"
        ],
    )

    fig_value.update_traces(
        textposition="inside",
        texttemplate="%{text:.1f}"
    )

    st.plotly_chart(fig_value, use_container_width=True)

with col2:
    st.subheader("Race-on-Race Value Change")
    st.caption("Compared with the previous race")

    growth_df = chart_df.sort_values(
        "team_value_change",
        ascending=True
    ).copy()

    growth_df["bar_color"] = growth_df["team_value_change"].apply(
        lambda x: "#8ECAE6" if x >= 0 else "#6C757D"
    )

    fig_growth = px.bar(
    growth_df,
    x="team_value_change",
    y="team_name",
    orientation="h",
    text="team_value_change",
    labels={
        "team_value_change": "Value Change ($m)",
        "team_name": "Team",
        }    
    )

    fig_growth.update_traces(
    marker=dict(color=growth_df["bar_color"].tolist()),
    textposition="inside",
    texttemplate="%{text:.1f}"
)

    fig_growth.update_layout(
        showlegend=False,
        yaxis_title=None
    )


    st.plotly_chart(fig_growth, use_container_width=True)

# Display Dataframe
st.dataframe(display_df)
