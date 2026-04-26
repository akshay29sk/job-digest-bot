# # =====================================
# LinkedIn Hiring Radar
# Version: v0.1.4.1
# File: app.py
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json

for key, value in st.secrets.items():
    os.environ[key] = value

st.title("🔥 LinkedIn Hiring Radar")

search = st.text_input("Search", "hiring customer success manager")

def run_backend():
    os.environ["SEARCH_QUERY"] = search

    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True
    )

    # 🔥 DEBUG
    if result.stderr:
        st.error("Backend Error")
        st.text(result.stderr)

    st.text("OUTPUT:")
    st.text(result.stdout[:1500])

    return result.stdout

if st.button("Run"):

    output = run_backend()

    try:
        results = json.loads(output)
    except:
        st.error("Parsing failed")
        st.stop()

    for r in results:
        st.write(r["content"][:200])
