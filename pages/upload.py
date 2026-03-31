import streamlit as st
from module.sidebar import show_sidebar

# Page config (must be FIRST Streamlit command)
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# Hide default page navigation
hide_nav = """
<style>
[data-testid="stSidebarNav"] {display: none;}
</style>
"""
st.markdown(hide_nav, unsafe_allow_html=True)

# Custom sidebar
selected_file, filter_option, receiver_email, send_btn = show_sidebar()

# Page content
st.title("Upload Files")

# Session storage
if "files" not in st.session_state:
    st.session_state.files = {}

# Upload
uploaded_files = st.file_uploader(
    "Upload Files",
    type=["txt", "csv", "pdf", "docx", "json"],
    accept_multiple_files=True
)

# Save files
if uploaded_files:
    for f in uploaded_files:
        st.session_state.files[f.name] = f

# Success message
if st.session_state.files:
    st.success(f"{len(st.session_state.files)} files uploaded")