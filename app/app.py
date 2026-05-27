import streamlit as st
import pandas as pd
import requests

API_URL = "http://127.0.0.1:8000"

st.title("F1 Fantasy Value Changes")

asset_type = st.selectbox(
    "Asset type",
    ["DRIVER", "CONSTRUCTOR"]
)

limit = st.slider(
    "Number of assets",
    5,
    30,
    20
)

response = requests.get(
    f"{API_URL}/assets/season-value-changes",
    params={
        "asset_type": asset_type,
        "limit": limit,
    },
)

data = response.json()
df = pd.DataFrame(data)

st.subheader(f"{asset_type.title()} season value changes")

st.dataframe(df)

st.bar_chart(
    df.set_index("display_name")["total_value_change"]
)