import streamlit as st
from config import API_URL
import pandas as pd
import requests
import plotly.express as px

st.title("F1 Fantasy Dashboard")
st.subheader("Race by Race")

response = requests.get(
    f"{API_URL}/league/team-values/latest"
)

data = response.json()
df = pd.DataFrame(data)