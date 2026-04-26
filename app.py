import streamlit as st
import subprocess
import os

st.title("🔥 LinkedIn Hiring Finder")

# Inputs
search = st.text_input("Search Query", "hiring business analyst")
roles = st.text_input("Role Keywords", "business analyst, product owner")
mode = st.selectbox("Email Mode", ["only_email", "prefer_email", "both"])
limit = st.slider("Results", 5, 20, 10)

if st.button("Run Search"):
    os.environ["SEARCH_QUERY"] = search
    os.environ["ROLE_KEYWORDS"] = roles
    os.environ["EMAIL_MODE"] = mode
    os.environ["RESULT_LIMIT"] = str(limit)

    output = subprocess.getoutput("python main.py")

    st.text_area("Results", output, height=400)
