import streamlit as st
import pandas as pd
import plotly.express as px
from src.connection import get_connection
from src.queries.warehouse import daily_total_credits, warehouse_total_credits
from src.utils import format_credits

st.set_page_config(page_title="Summary", layout="wide")
st.title("Summary")

start_date = st.session_state.get("start_date")
end_date = st.session_state.get("end_date")

if start_date is None or end_date is None:
    st.warning("Return to the home page to set a date range.")
    st.stop()


@st.cache_data(ttl=300)
def fetch_daily_totals(_start: str, _end: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(daily_total_credits(), (_start, _end))
        return cur.fetch_pandas_all()
    finally:
        conn.close()


@st.cache_data(ttl=300)
def fetch_warehouse_totals(_start: str, _end: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(warehouse_total_credits(), (_start, _end))
        return cur.fetch_pandas_all()
    finally:
        conn.close()


start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

df_daily = fetch_daily_totals(start_str, end_str)
df_wh = fetch_warehouse_totals(start_str, end_str)

total = df_daily["TOTAL_CREDITS"].sum() if not df_daily.empty else 0.0
avg_daily = df_daily["TOTAL_CREDITS"].mean() if not df_daily.empty else 0.0
top_wh = df_wh.iloc[0]["WAREHOUSE_NAME"] if not df_wh.empty else "N/A"

col1, col2, col3 = st.columns(3)
col1.metric("Total Credits", format_credits(total))
col2.metric("Avg Daily Credits", format_credits(avg_daily))
col3.metric("Top Warehouse", top_wh)

st.subheader("Daily Credits Trend")
if not df_daily.empty:
    fig = px.line(
        df_daily,
        x="USAGE_DATE",
        y="TOTAL_CREDITS",
        labels={"USAGE_DATE": "Date", "TOTAL_CREDITS": "Credits"},
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available for the selected date range.")

st.subheader("Top Cost Drivers")
if not df_wh.empty:
    st.dataframe(
        df_wh[["WAREHOUSE_NAME", "TOTAL_CREDITS", "COMPUTE_CREDITS", "CLOUD_CREDITS"]],
        use_container_width=True,
    )
else:
    st.info("No warehouse data available.")
