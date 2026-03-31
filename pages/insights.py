import streamlit as st
import matplotlib.pyplot as plt

st.title("Insights")

if "df" not in st.session_state:
    st.warning("Run analysis first")
    st.stop()

df = st.session_state.df
scores = st.session_state.scores

filter_option = st.selectbox("Filter", ["All"] + list(scores.keys()))

if filter_option == "All":
    filtered_df = df
else:
    filtered_df = df[df["Result"] == filter_option]

st.dataframe(filtered_df)

# Chart
labels = list(scores.keys())
values = list(scores.values())

fig, ax = plt.subplots()
ax.bar(labels, values)
st.pyplot(fig)