import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Snowflake Cost Intelligence", layout="wide")
st.title("Snowflake Cost Intelligence Dashboard")

with st.sidebar:
    st.header("Settings")
    preset = st.selectbox("Date Range", ["Last 7 days", "Last 30 days", "Last 90 days"], index=1)
    days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
    days = days_map[preset]
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days)
    st.session_state["start_date"] = start_date
    st.session_state["end_date"] = end_date
    st.caption(f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

st.markdown("Use the sidebar to navigate between dashboard pages.")
