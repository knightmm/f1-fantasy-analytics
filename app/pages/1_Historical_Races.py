import streamlit as st
from config import API_URL
import pandas as pd
import requests
import plotly.express as px

st.title("F1 Fantasy Dashboard")
st.header("Race by Race")

response = requests.get(
    f"{API_URL}/league/team-values/by-race"
)

data = response.json()
df = pd.DataFrame(data)

race_options = sorted(df["race_number"].unique())

selected_race = st.selectbox(
    "Select race",
    race_options,
    index=len(race_options) - 1
)

race_df = (
    df[df["race_number"] == selected_race]
    .reset_index(drop=True)
)

race_df.index = race_df.index + 1

st.subheader(f"Race {selected_race} Team Values")
st.dataframe(race_df)

fig = px.bar(
    race_df,
    x="team_name",
    y="team_value",
    text="team_value",
    hover_data=["user_name", "team_value_change", "calculated_asset_points"],
)

fig.update_traces(textposition="inside")
st.plotly_chart(fig, use_container_width=True)

