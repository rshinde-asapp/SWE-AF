import pandas as pd
import plotly.express as px
import streamlit as st

from src.connection import get_connection
from src.queries.query_costs import (
    credits_by_query_type,
    credits_by_user,
    top_queries_by_cost,
)
from src.utils import format_credits, get_date_range

st.set_page_config(page_title="Query Costs", layout="wide")
st.title("Query Costs")

start_date, end_date = get_date_range()

try:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(top_queries_by_cost(), (start_date, end_date))
    top_df = pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])

    cur.execute(credits_by_query_type(), (start_date, end_date))
    type_df = pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])

    cur.execute(credits_by_user(), (start_date, end_date))
    user_df = pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])

    cur.close()
    conn.close()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()

st.subheader("Top Queries by Cost")
if not top_df.empty:
    top_df["CREDITS_USED_CLOUD_SERVICES"] = top_df[
        "CREDITS_USED_CLOUD_SERVICES"
    ].apply(format_credits)
    st.dataframe(top_df, use_container_width=True)
else:
    st.info("No query cost data for the selected period.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Credits by Query Type")
    if not type_df.empty:
        fig = px.pie(
            type_df,
            names="QUERY_TYPE",
            values="TOTAL_CREDITS",
            title="Credits by Query Type",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for the selected period.")

with col2:
    st.subheader("Credits by User")
    if not user_df.empty:
        fig = px.bar(
            user_df,
            x="USER_NAME",
            y="TOTAL_CREDITS",
            title="Credits by User",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for the selected period.")
