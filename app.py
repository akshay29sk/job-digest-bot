# =====================================
# LinkedIn Hiring Radar
# Version: v0.1.8
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

search = st.text_input(
    "🔎 Search Query",
    value="hiring product owner",
    placeholder="e.g. hiring product owner, business analyst, product manager"
)

posted_limit = st.selectbox(
    "🕒 Posted Within",
    ["any", "1h", "24h", "week", "month"],
    index=2
)

mode = st.selectbox(
    "📧 Email Mode",
    ["prefer_email", "only_email", "both", "no_email"]
)

col1, col2 = st.columns(2)
run_btn = col1.button("🚀 Run Search")
refresh_btn = col2.button("🔄 Refresh")

def run_backend():
    os.environ["SEARCH_QUERY"] = search
    os.environ["EMAIL_MODE"] = mode
    os.environ["POSTED_LIMIT"] = posted_limit

    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True
    )

    return result

if run_btn or refresh_btn:

    with st.spinner("Fetching jobs..."):
        result = run_backend()

    # Debug
    with st.expander("🧪 Debug Info", expanded=False):
        if result.returncode != 0:
            st.error("Backend Error")
            st.text(result.stderr)
        else:
            st.success("Backend OK")

        st.text(result.stdout[:1000])

    # Parse JSON
    match = re.search(r"\[.*\]", result.stdout, re.DOTALL)
    results = json.loads(match.group(0)) if match else []

    st.markdown("## 🎯 Results")

    if not results:
        st.warning("No results found")
    else:
        for r in results:
            st.markdown("---")

            st.caption(f"⭐ {r['score']} | 🧠 {r['semantic_score']}")

            if r["email"] != "Not found":
                st.success(r["email"])
            else:
                st.caption("No Email")

            st.write(r["content"][:400])
            st.markdown(f"[🔗 Open Post]({r['link']})")
