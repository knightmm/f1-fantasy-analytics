import streamlit as st
from config import API_URL
import pandas as pd
import requests
import plotly.express as px

st.title("F1 Fantasy Dashboard")
st.subheader("Current Standings")

response = requests.get(
    f"{API_URL}/league/team-values/latest"
)

data = response.json()
df = pd.DataFrame(data)

exclude_limitless = st.checkbox(
    "Exclude likely limitless teams",
    value=True
)

if exclude_limitless:
    df = df[
        df["likely_limitless_team"] == 0
    ]

display_df = df[
    [
        "team_name",
        "user_name",
        "current_team_value",
        "total_team_value_change",
        "latest_completed_team_points",
    ]
]

col1, col2 = st.columns(2)

with col1:
    st.subheader("Team Value Leaderboard")

    team_value_df = display_df.sort_values(
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

    growth_df = display_df.sort_values(
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
    
    fig_value.update_traces(
        textposition="inside",
        texttemplate="%{text:.1f}"
    )
    st.plotly_chart(fig_growth, use_container_width=True)