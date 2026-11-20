import base64
import streamlit as st

st.title("Biography")
st.caption("Retail Sales as a Composition of the M5 Competition Dataset from Walmart · Elaine Key ")

#little image reader
img = base64.b64encode(open("assets/profile.svg", "rb").read()).decode()

st.markdown(f'<img src="data:image/svg+xml;base64,{img}" width="160" alt="">',
            unsafe_allow_html=True)

st.subheader("Summary")

st.write("I am a data analytics student at MSU Denver, focused on creating clean models to produce actionable decisions. "

         "This project explores weekly item-level sales to ask how price changes, "

         "SNAP benefit days, store differences and department trends shape revenue.")

st.markdown("""

- **Tools:** Python, pandas, Plotly, Streamlit

- **Skills:** feature engineering (revenue = units × sell price), group comparisons, exploratory analysis

- **Focus:** pricing analytics and retail performance benchmarking
""")
