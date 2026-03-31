import streamlit as st
import pandas as pd
from io import StringIO
from pipeline import clean, analyze_text, read_json

st.title("Results")

if "files" not in st.session_state or not st.session_state.files:
    st.warning("Upload files first")
    st.stop()

file_name = st.selectbox("Select File", list(st.session_state.files.keys()))
file = st.session_state.files[file_name]

df = None
text_data = []

# CSV Example
if file.type == "text/csv":
    stringio = StringIO(file.getvalue().decode("utf-8"))
    df = pd.read_csv(stringio)
    st.dataframe(df)

    col = st.selectbox("Text Column", df.columns)
    text_data = df[col].astype(str)

# Run analysis
if st.button("Run Analysis"):
    results = []
    scores = {"Positive":0,"Negative":0,"Neutral":0,"Spam":0,"Suggestion":0,"Complaint":0}

    for t in text_data:
        t = clean(t)
        r = analyze_text(t)
        results.append(r)
        scores[r] += 1

    df["Result"] = results
    st.session_state.df = df
    st.session_state.scores = scores

    st.success("Analysis Done")