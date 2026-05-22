import streamlit as st
import pandas as pd
import requests

API_URL = "http://127.0.0.1:8000"

st.title("F1 Fantasy Value Changes")

limit = st.slider("Number of constructors", 5, 10, 10)

response = requests.get(
    f"{API_URL}/constructors/season-value-changes",
    params={"limit": limit},
)

data = response.json()
df = pd.DataFrame(data)

st.subheader("Constructor season value changes")
st.dataframe(df)

st.bar_chart(
    df.set_index("display_name")["total_value_change"]
)