import streamlit as st
from config import API_URL
import pandas as pd
import requests
import plotly.express as px

st.title("🏁 F1 Fantasy Dashboard")

# Latest team values
response = requests.get(f"{API_URL}/league/team-values/latest")
df = pd.DataFrame(response.json())

df["last_race_rank"] = (
    df["latest_completed_team_points"]
    .rank(method="min", ascending=False)
    .astype(int)
)

# Season standings
response = requests.get(f"{API_URL}/league/team-season-summary")
season_df = pd.DataFrame(response.json())

season_df["overall_rank"] = (
    season_df["cumulative_calculated_points"]
    .rank(method="min", ascending=False)
    .astype(int)
)

DEFAULT_TEAM = "In Search of Lost Sainz"

team_options = sorted(df["team_name"].tolist())
default_index = team_options.index(DEFAULT_TEAM)

selected_team = st.selectbox(
    "Select team",
    team_options,
    index=default_index
)

my_row = df[df["team_name"] == selected_team].iloc[0]
my_season_row = season_df[season_df["team_name"] == selected_team].iloc[0]

st.subheader(f"{selected_team} Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Overall Rank",
    int(my_season_row["overall_rank"])
)

col2.metric(
    "Last Race Rank",
    int(my_row["last_race_rank"])
)

col3.metric(
    "Last Race Points",
    int(my_row["latest_completed_team_points"])
)

col4.metric(
    "Team Value",
    f"${my_row['current_team_value']:.1f}m",
    f"{my_row['total_team_value_change']:+.1f}m"
)


# Season Standings
season_display_df = season_df[
    [
        "team_name",
        "user_name",
        "cumulative_calculated_points",
        "latest_team_value",
        "latest_team_value_change",
        "latest_calculated_asset_points",
        "has_used_limitless",
    ]
].rename(
    columns={
        "team_name": "Team",
        "user_name": "User",
        "cumulative_calculated_points": "Total Points",
        "latest_team_value": "Team Value",
        "latest_team_value_change": "Value Change",
        "latest_calculated_asset_points": "Latest Race Points",
        "has_used_limitless": "Limitless Used",
    }
)

season_display_df.index = season_display_df.index + 1

st.subheader("Season Overall")
st.dataframe(season_display_df)


# Latest Team Values

st.subheader("Last Race Results")
exclude_limitless = st.checkbox(
    "Exclude likely limitless teams",
    value=True
)

if exclude_limitless:
    chart_df = df[df["likely_limitless_team"] == 0]
else:
    chart_df = df

display_df = df[
    [
        "team_name",
        "user_name",
        "latest_completed_team_points",
        "total_team_value_change",
        "current_team_value",
        "likely_limitless_team",
    ]
].rename(
    columns={
        "team_name": "Team",
        "user_name": "User",
        "latest_completed_team_points": "Last Race Points",
        "total_team_value_change": "Value Change",
        "current_team_value": "Team Value",
        "likely_limitless_team": "Limitless Chip",
    }
)

display_df.index = display_df.index + 1
st.dataframe(display_df)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Team Value Leaderboard")

    team_value_df = chart_df.sort_values(
        "current_team_value",
        ascending=True
    )

    fig_value = px.bar(
        team_value_df,
        x="current_team_value",
        y="team_name",
        orientation="h",
        text="current_team_value",
    )

    fig_value.update_traces(
        textposition="inside",
        texttemplate="%{text:.1f}"
    )    
    st.plotly_chart(fig_value, use_container_width=True)

with col2:
    st.subheader("Team Value Growth")

    growth_df = chart_df.sort_values(
        "total_team_value_change",
        ascending=True
    )

    fig_growth = px.bar(
        growth_df,
        x="total_team_value_change",
        y="team_name",
        orientation="h",
        text="total_team_value_change",
    )
    
    fig_growth.update_traces(
        textposition="inside",
        texttemplate="%{text:.1f}"
    )
    st.plotly_chart(fig_growth, use_container_width=True)