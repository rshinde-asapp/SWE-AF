import streamlit as st
import pandas as pd
import plotly.express as px
from src.connection import get_connection
from src.queries.warehouse import warehouse_credits_daily, warehouse_total_credits

st.set_page_config(page_title="Warehouse Utilization", layout="wide")
st.title("Warehouse Utilization")

start_date = st.session_state.get("start_date")
end_date = st.session_state.get("end_date")

if start_date is None or end_date is None:
    st.warning("Return to the home page to set a date range.")
    st.stop()


@st.cache_data(ttl=300)
def fetch_credits_daily(_start: str, _end: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(warehouse_credits_daily(), (_start, _end))
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

df_daily = fetch_credits_daily(start_str, end_str)
df_totals = fetch_warehouse_totals(start_str, end_str)

warehouses = df_daily["WAREHOUSE_NAME"].unique().tolist() if not df_daily.empty else []
selected = st.multiselect("Select Warehouses", warehouses, default=warehouses)

if selected:
    df_filtered = df_daily[df_daily["WAREHOUSE_NAME"].isin(selected)]
else:
    df_filtered = df_daily

st.subheader("Credits by Warehouse (Stacked Bar)")
if not df_filtered.empty:
    fig = px.bar(
        df_filtered,
        x="USAGE_DATE",
        y="TOTAL_CREDITS",
        color="WAREHOUSE_NAME",
        labels={"USAGE_DATE": "Date", "TOTAL_CREDITS": "Credits", "WAREHOUSE_NAME": "Warehouse"},
        barmode="stack",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for selected warehouses.")

st.subheader("Warehouse Totals")
if not df_totals.empty:
    st.dataframe(
        df_totals[["WAREHOUSE_NAME", "TOTAL_CREDITS", "COMPUTE_CREDITS", "CLOUD_CREDITS"]],
        use_container_width=True,
    )
else:
    st.info("No warehouse data available.")

st.subheader("Drill-Down: Daily Detail")
if warehouses:
    drill_wh = st.selectbox("Select Warehouse", warehouses)
    df_drill = df_daily[df_daily["WAREHOUSE_NAME"] == drill_wh]
    if not df_drill.empty:
        fig2 = px.bar(
            df_drill,
            x="USAGE_DATE",
            y=["COMPUTE_CREDITS", "CLOUD_CREDITS"],
            labels={"USAGE_DATE": "Date", "value": "Credits", "variable": "Type"},
            barmode="stack",
            title=f"{drill_wh} — Compute vs Cloud Credits",
        )
        st.plotly_chart(fig2, use_container_width=True)
