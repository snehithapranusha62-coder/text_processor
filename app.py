import streamlit as st
import pandas as pd
import json
from docx import Document
from textblob import TextBlob
import pdfplumber
import smtplib
from email.message import EmailMessage
from io import BytesIO, StringIO
import re
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Multi File Analyzer")

# ---------------- EMAIL CONFIG ----------------
EMAIL ="snehithapranusha@gmail.com"  
PASSWORD ="jcwyqypxtdvq"

# ---------------- SESSION ----------------
if "files" not in st.session_state:
    st.session_state.files = {}

# ---------------- FILE UPLOADER ----------------
uploaded_files = st.file_uploader(
    "Upload Files",
    type=["txt", "csv", "pdf", "docx", "json"],
    accept_multiple_files=True
)

# Keep previously uploaded files
if uploaded_files:
    for f in uploaded_files:
        if f.name not in st.session_state.files:
            st.session_state.files[f.name] = f

# ---------------- SIDEBAR ----------------
st.sidebar.title("Controls")
selected_file = None
if st.session_state.files:
    selected_file = st.sidebar.radio(
        "Uploaded Files",
        list(st.session_state.files.keys())
    )

filter_option = st.sidebar.selectbox(
    "Filter",
    ["All", "Positive", "Negative", "Neutral", "Spam", "Suggestion", "Complaint"]
)

receiver_email = st.sidebar.text_input("Enter Email")

# ---------------- FUNCTIONS ----------------
def clean(text):
    return re.sub(r'[\x00-\x1F]', '', str(text))

def analyze_text(text):
    t = text.lower()
    if any(w in t for w in ["buy now","free","click here"]):
        return "Spam"
    elif any(w in t for w in ["should","suggest","recommend"]):
        return "Suggestion"
    elif any(w in t for w in ["bad","worst","problem","issue","useless","not working"]):
        return "Complaint"
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

def read_json(file):
    content = file.getvalue().decode("utf-8")
    data = [json.loads(line) for line in content.splitlines() if line.strip()]
    return pd.DataFrame(data)

# ---------------- READ FILE ----------------
df = None
text_data = []

if selected_file:
    file = st.session_state.files[selected_file]
    st.subheader("Preview")

    # TXT
    if file.type == "text/plain":
        text = file.getvalue().decode("utf-8")
        st.text_area("", text, height=250)
        text_data = text.splitlines()
        df = pd.DataFrame({"Text": text_data})

    # CSV
    elif file.type == "text/csv":
        # Use StringIO to avoid pandas read_csv error
        stringio = StringIO(file.getvalue().decode("utf-8"))
        df = pd.read_csv(stringio)
        st.dataframe(df)
        # Only text columns
        text_cols = [col for col in df.columns if df[col].astype(str).str.contains('[A-Za-z]', regex=True).any()]
        col = st.selectbox("Select Text Column", text_cols)
        text_data = df[col].astype(str)

    # PDF
    elif file.type == "application/pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for p in pdf.pages:
                text += p.extract_text() or ""
        st.text_area("", text[:2000], height=250)
        text_data = text.splitlines()
        df = pd.DataFrame({"Text": text_data})

    # DOCX
    elif file.type.endswith("document"):
        doc = Document(file)
        text_data = [p.text for p in doc.paragraphs]
        st.text_area("", "\n".join(text_data), height=250)
        df = pd.DataFrame({"Text": text_data})

    # JSON
    elif file.name.endswith(".json"):
        df = read_json(file)
        st.dataframe(df)
        text_cols = [col for col in df.columns if df[col].astype(str).str.contains('[A-Za-z]', regex=True).any()]
        col = st.selectbox("Select Text Column", text_cols)
        text_data = df[col].astype(str)

# ---------------- ANALYSIS ----------------
if st.button("Run Analysis") and df is not None:
    results = []
    scores = {"Positive":0, "Negative":0, "Neutral":0, "Spam":0, "Suggestion":0, "Complaint":0}

    for t in text_data:
        t = clean(t)
        result = analyze_text(t)
        results.append(result)
        scores[result] += 1

    df["Result"] = results
    st.session_state.df = df
    st.session_state.scores = scores

# ---------------- DISPLAY ----------------
if "df" in st.session_state:
    df = st.session_state.df
    scores = st.session_state.scores

    # Show scores
    st.subheader("Scores")
    cols = st.columns(6)
    for i,key in enumerate(scores):
        cols[i].metric(key, scores[key])

    # Filter data
    if filter_option == "All":
        filtered_df = df
        filtered_scores = scores
    else:
        filtered_df = df[df["Result"] == filter_option]
        filtered_scores = {filter_option: scores.get(filter_option,0)}

    st.subheader(f"{filter_option} Data")
    st.dataframe(filtered_df)

    # Bar chart
    labels = list(scores.keys())
    values = list(scores.values())
    colors = ["gray"]*len(labels)
    if filter_option in labels:
        colors[labels.index(filter_option)] = "gold"

    fig, ax = plt.subplots()
    ax.bar(labels, values, color=colors, width=0.4)
    st.pyplot(fig)

    chart_buf = BytesIO()
    fig.savefig(chart_buf, format="png")

    # Excel
    output = BytesIO()
    summary = pd.DataFrame(list(filtered_scores.items()), columns=["Type","Count"])
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="Data")
        summary.to_excel(writer, index=False, sheet_name="Summary")
    excel_data = output.getvalue()

    st.download_button("Download Excel", excel_data)

    # Send email
    if st.sidebar.button("Send Email"):
        if receiver_email:
            score_text = ""
            for k,v in filtered_scores.items():
                score_text += f"{k} : {v}\n"
            try:
                msg = EmailMessage()
                msg["Subject"] = "Analysis Report"
                msg["From"] = EMAIL
                msg["To"] = receiver_email
                msg.set_content(score_text)
                msg.add_attachment(
                    excel_data,
                    maintype="application",
                    subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename="report.xlsx"
                )
                msg.add_attachment(
                    chart_buf.getvalue(),
                    maintype="image",
                    subtype="png",
                    filename="chart.png"
                )
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login(EMAIL, PASSWORD)
                    smtp.send_message(msg)
                st.sidebar.success("Email Sent")
            except Exception as e:
                st.sidebar.error(e)
        else:
            st.sidebar.warning("Enter Email")