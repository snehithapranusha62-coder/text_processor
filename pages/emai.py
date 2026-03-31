import streamlit as st
import pandas as pd
from io import BytesIO
import smtplib
from email.message import EmailMessage

st.title("Export & Email")
EMAIL ="snehithapranusha62@gmail.com"  
PASSWORD ="jcwyqypxtdvqaaki"

if "df" not in st.session_state:
    st.warning("No data")
    st.stop()

df = st.session_state.df
scores = st.session_state.scores

# Excel export
output = BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, index=False)

excel_data = output.getvalue()

st.download_button("Download Excel", excel_data)

receiver = st.text_input("Receiver Email")

if st.button("Send Email"):
    if receiver:
        msg = EmailMessage()
        msg["Subject"] = "Report"
        msg["From"] = EMAIL
        msg["To"] = receiver

        msg.set_content(str(scores))
        msg.add_attachment(excel_data,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="report.xlsx"
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)

        st.success("Email Sent")