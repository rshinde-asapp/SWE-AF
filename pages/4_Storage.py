import streamlit as st
import pandas as pd
import plotly.express as px

from src.connection import get_connection
from src.queries.storage import total_storage_daily, storage_by_database

st.set_page_config(page_title="Storage Costs", layout="wide")
st.title("Storage Costs")

start = st.session_state.get("start_date")
end = st.session_state.get("end_date")

if not start or not end:
    st.warning("Please set a date range using the sidebar on the main page.")
    st.stop()

start_str = start.strftime("%Y-%m-%d")
end_str = end.strftime("%Y-%m-%d")


@st.cache_data(ttl=300)
def fetch_total_storage(_start: str, _end: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(total_storage_daily(), (_start, _end))
        return cur.fetch_pandas_all()
    finally:
        conn.close()


@st.cache_data(ttl=300)
def fetch_storage_by_database(_start: str, _end: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(storage_by_database(), (_start, _end))
        return cur.fetch_pandas_all()
    finally:
        conn.close()


# Section 1: Total storage trend
st.subheader("Total Storage Trend")
df_total = fetch_total_storage(start_str, end_str)
if df_total.empty:
    st.info("No storage data available for the selected period.")
else:
    fig_trend = px.line(
        df_total,
        x="USAGE_DATE",
        y="TOTAL_BYTES",
        title="Total Storage (bytes) Over Time",
        labels={"USAGE_DATE": "Date", "TOTAL_BYTES": "Total Bytes"},
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# Section 2: Per-database storage bar chart
st.subheader("Storage by Database")
df_db = fetch_storage_by_database(start_str, end_str)
if df_db.empty:
    st.info("No per-database storage data available for the selected period.")
else:
    fig_db = px.bar(
        df_db,
        x="DATABASE_NAME",
        y="AVG_DATABASE_BYTES",
        title="Average Database Storage by Database",
        labels={"DATABASE_NAME": "Database", "AVG_DATABASE_BYTES": "Avg Bytes"},
    )
    st.plotly_chart(fig_db, use_container_width=True)

# Section 3: Storage type breakdown stacked area chart
st.subheader("Storage Type Breakdown")
if df_total.empty:
    st.info("No storage data available for the selected period.")
else:
    df_melt = df_total.melt(
        id_vars=["USAGE_DATE"],
        value_vars=["AVERAGE_STAGE_BYTES", "AVERAGE_DATABASE_BYTES", "AVERAGE_FAILSAFE_BYTES"],
        var_name="Storage Type",
        value_name="Bytes",
    )
    fig_area = px.area(
        df_melt,
        x="USAGE_DATE",
        y="Bytes",
        color="Storage Type",
        title="Storage by Type Over Time",
        labels={"USAGE_DATE": "Date", "Bytes": "Bytes"},
    )
    st.plotly_chart(fig_area, use_container_width=True)
