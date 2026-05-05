import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.connection import get_connection
from src.queries.anomalies import warehouse_daily_with_zscore

st.set_page_config(page_title="Anomalies", page_icon="⚠️", layout="wide")
st.title("⚠️ Warehouse Credit Anomalies")

threshold = st.slider(
    "Z-Score Threshold",
    min_value=1.5,
    max_value=3.0,
    value=2.0,
    step=0.1,
    help="Points with |z_score| above this threshold are flagged as anomalies.",
)

start_date = st.session_state.get("start_date")
end_date = st.session_state.get("end_date")

if start_date is None or end_date is None:
    st.info("Set a date range in the sidebar on the main page.")
    st.stop()

try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(warehouse_daily_with_zscore(), (start_date, end_date))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)
    cursor.close()
    conn.close()
except Exception as exc:
    st.error(f"Failed to load data: {exc}")
    st.stop()

if df.empty:
    st.warning("No data returned for the selected date range.")
    st.stop()

df["USAGE_DATE"] = pd.to_datetime(df["USAGE_DATE"])
df["IS_ANOMALY"] = df["Z_SCORE"].abs() > threshold

warehouses = df["WAREHOUSE_NAME"].unique().tolist()
selected = st.multiselect("Warehouses", warehouses, default=warehouses)
filtered = df[df["WAREHOUSE_NAME"].isin(selected)]

fig = go.Figure()
for wh in selected:
    wh_df = filtered[filtered["WAREHOUSE_NAME"] == wh]
    normal = wh_df[~wh_df["IS_ANOMALY"]]
    anomalous = wh_df[wh_df["IS_ANOMALY"]]

    fig.add_trace(
        go.Scatter(
            x=wh_df["USAGE_DATE"],
            y=wh_df["DAILY_CREDITS"],
            mode="lines",
            name=wh,
            line={"width": 1},
            showlegend=True,
        )
    )
    if not normal.empty:
        fig.add_trace(
            go.Scatter(
                x=normal["USAGE_DATE"],
                y=normal["DAILY_CREDITS"],
                mode="markers",
                name=f"{wh} normal",
                marker={"size": 5},
                showlegend=False,
            )
        )
    if not anomalous.empty:
        fig.add_trace(
            go.Scatter(
                x=anomalous["USAGE_DATE"],
                y=anomalous["DAILY_CREDITS"],
                mode="markers",
                name=f"{wh} anomaly",
                marker={"size": 12, "color": "red", "symbol": "x"},
                showlegend=True,
            )
        )

fig.update_layout(
    title="Daily Credits with Anomalies",
    xaxis_title="Date",
    yaxis_title="Credits Used",
    legend_title="Warehouse",
)
st.plotly_chart(fig, use_container_width=True)

anomaly_df = filtered[filtered["IS_ANOMALY"]].copy()
if anomaly_df.empty:
    st.success(f"No anomalies detected at threshold {threshold}.")
else:
    st.subheader(f"Anomalous Points (|Z-Score| > {threshold})")
    st.dataframe(
        anomaly_df[
            ["WAREHOUSE_NAME", "USAGE_DATE", "DAILY_CREDITS", "ROLLING_AVG", "ROLLING_STDDEV", "Z_SCORE"]
        ].sort_values("Z_SCORE", key=lambda s: s.abs(), ascending=False),
        use_container_width=True,
    )
