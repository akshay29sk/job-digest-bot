# =====================================
# LinkedIn Hiring Radar
# Version: v0.1.1
# File: app.py
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json
import re

# Load secrets
for key, value in st.secrets.items():
    os.environ[key] = value

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

st.title("🔥 LinkedIn Hiring Radar")

search = st.text_input("🔎 Search Query", "hiring customer success manager")

posted_limit = st.selectbox(
    "🕒 Posted Within",
    ["any", "1h", "24h", "week", "month"],
    index=2
)

mode = st.selectbox(
    "📧 Email Mode",
    ["prefer_email", "only_email", "both", "no_email"]
)

cache_file = "cache.json"

def run_backend():
    os.environ["SEARCH_QUERY"] = search
    os.environ["POSTED_LIMIT"] = posted_limit
    os.environ["EMAIL_MODE"] = mode

    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True
    )

    return result.stdout

if st.button("🚀 Run Search"):

    output = run_backend()

    try:
        match = re.search(r"\[.*\]", output, re.DOTALL)
        results = json.loads(match.group(0))
    except:
        st.error("Parsing failed")
        st.text(output)
        st.stop()

    st.markdown("## 🎯 Results")

    for r in results:
        st.markdown("---")

        st.caption(f"⭐ Score: {r['score']} | 🧠 Semantic: {r['semantic_score']}")

        if r["email"] != "Not found":
            st.success(r["email"])
        else:
            st.caption("❌ No Email")

        st.write(r["content"][:300])
        st.markdown(f"[🔗 Open Post]({r['link']})")
