import streamlit as st
import pandas as pd
import json
from docx import Document
from textblob import TextBlob
import pdfplumber
import smtplib
from email.message import EmailMessage
from io import BytesIO

st.set_page_config(layout="wide")
st.title("📂 Multi File Analyzer")

# ---------------- SESSION STORAGE ----------------
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

# ---------------- FILE UPLOADER ----------------
uploaded_files = st.file_uploader(
    "Upload files",
    type=["txt", "csv", "pdf", "docx", "json"],
    accept_multiple_files=True
)

if uploaded_files:
    for file in uploaded_files:
        st.session_state.uploaded_files[file.name] = file

# ---------------- SIDEBAR ----------------
st.sidebar.title("📁 Uploaded Files")

if st.session_state.uploaded_files:
    selected_file = st.sidebar.radio(
        "Select a file",
        list(st.session_state.uploaded_files.keys())
    )
else:
    st.sidebar.info("No files uploaded")
    selected_file = None


# ---------------- SENTIMENT FUNCTION ----------------
def get_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"


# ---------------- EMAIL FUNCTION ----------------
def send_email(receiver_email, excel_bytes):
    sender_email = "snehithapranusha62@gmail.com"
    sender_password = "jcwyqypxtdvqaaki"  

    try:
        msg = EmailMessage()
        msg["Subject"] = "Sentiment Analysis Report"
        msg["From"] = sender_email
        msg["To"] = receiver_email

        msg.set_content("Attached is your sentiment analysis report.")

        msg.add_attachment(
            excel_bytes,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="sentiment_report.xlsx"
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)

        return True
    except Exception as e:
        return str(e)


# ---------------- JSON READER ----------------
def read_json(file):
    content = file.getvalue().decode("utf-8")
    data = [json.loads(line) for line in content.splitlines() if line.strip()]
    return pd.DataFrame(data)


# ---------------- MAIN AREA ----------------
st.subheader("File Preview & Sentiment Analysis")

if selected_file:
    file = st.session_state.uploaded_files[selected_file]
    file_type = file.type

    text_data = []
    df = None

    # -------- TXT --------
    if file_type == "text/plain":
        text = file.getvalue().decode("utf-8")
        st.text_area("Preview", text, height=300)
        text_data = text.splitlines()
        df = pd.DataFrame({"Text": text_data})

    # -------- CSV --------
    elif file_type == "text/csv":
        df = pd.read_csv(file)
        st.dataframe(df)
        column = st.selectbox("Select column for analysis", df.columns)
        text_data = df[column].astype(str)

    # -------- DOCX --------
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file)
        text_data = [p.text for p in doc.paragraphs]
        st.text_area("Preview", "\n".join(text_data), height=300)
        df = pd.DataFrame({"Text": text_data})

    # -------- JSON --------
    elif file_type == "application/json" or file.name.endswith(".json"):
        df = read_json(file)
        st.dataframe(df)
        field = st.selectbox("Select field for analysis", df.columns)
        text_data = df[field].astype(str)

    # -------- PDF --------
    elif file_type == "application/pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        st.text_area("Preview", text[:2000], height=300)
        text_data = text.splitlines()
        df = pd.DataFrame({"Text": text_data})

    else:
        st.warning("Unsupported file type")

    # ---------------- ANALYZE ----------------
    if st.button("Calculate Sentiment Score"):
        sentiments = []
        positive = 0
        negative = 0
        neutral = 0

        for sentence in text_data:
            sentiment = get_sentiment(str(sentence))
            sentiments.append(sentiment)
            if sentiment == "Positive":
                positive += 1
            elif sentiment == "Negative":
                negative += 1
            else:
                neutral += 1

        df["Sentiment"] = sentiments

        # ---------------- DISPLAY SCORES ----------------
        st.subheader("Sentiment Scores")
        col1, col2, col3 = st.columns(3)
        col1.success(f"Positive Score: {positive}")
        col2.error(f"Negative Score: {negative}")
        col3.info(f"Neutral Score: {neutral}")

        # ---------------- SHOW TABLE ----------------
        st.subheader("Result Table")
        st.dataframe(df)

        # ---------------- SUMMARY TABLE ----------------
        summary_df = pd.DataFrame({
            "Metric": ["Positive Score", "Negative Score", "Neutral Score"],
            "Value": [positive, negative, neutral]
        })

        # ---------------- CREATE EXCEL ----------------
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Sentiment Results")
            summary_df.to_excel(writer, index=False, sheet_name="Summary Scores")
        excel_data = output.getvalue()

        # Store in session state
        st.session_state["excel_file"] = excel_data

        # ---------------- DOWNLOAD BUTTON ----------------
        st.download_button(
            label="⬇ Download Excel Report",
            data=excel_data,
            file_name="sentiment_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ---------------- EMAIL SECTION ----------------
st.subheader("Send Report via Email")
email = st.text_input("Enter Email Address")

if st.button("Send Email"):
    if email == "":
        st.warning("Please enter an email address")
    elif "excel_file" not in st.session_state:
        st.warning("Please calculate sentiment first to generate Excel file")
    else:
        with st.spinner("Sending email..."):
            result = send_email(email, st.session_state["excel_file"])
        if result == True:
            st.success("Email sent successfully!")
        else:
            st.error(f"Email failed: {result}")