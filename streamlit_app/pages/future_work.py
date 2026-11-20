import streamlit as st

st.title("Future Work")
st.caption("Retail Sales Explorer · Elaine Key")

st.subheader("Next up / To do")
st.markdown("""
- Add a weekly demand forecast and compare accuracy by department.
- Estimate item-level elasticity with a regression model
- Model day-of-month and day-of-week alongside SNAP days to separate calendar effects.
""")

st.caption("Edit these so they describe your own prototype.")
st.markdown("""
- One long sketched page became four pages with sidebar navigation.
- Sketched filters became working controls that update every KPI and chart.
""")
