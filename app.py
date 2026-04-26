# =====================================
# LinkedIn Hiring Radar
# Version: v0.2.3
# File: app.py
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json
import re

for key, value in st.secrets.items():
    os.environ[key] = value

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

# Analytics
DATA_FILE = "analytics.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"visits": 0, "searches": 0}
    return json.load(open(DATA_FILE))

def save_data(data):
    json.dump(data, open(DATA_FILE, "w"))

data = load_data()
data["visits"] += 1
save_data(data)

st.title("🔥 LinkedIn Hiring Radar")

search = st.text_input("🔎 Role", "product owner")

posted_limit = st.selectbox(
    "🕒 Posted Within",
    ["any", "1h", "24h", "week", "month"],
    index=2
)

mode = st.selectbox(
    "📧 Email Mode",
    ["prefer_email", "only_email", "both", "no_email"]
)

cache_key = f"{search}_{posted_limit}_{mode}".replace(" ", "_")
CACHE_FILE = f"cache_{cache_key}.json"

col1, col2 = st.columns(2)
run_btn = col1.button("🚀 Run Search")
refresh_btn = col2.button("🔄 Refresh")

def run_backend():
    os.environ["SEARCH_QUERY"] = search
    os.environ["EMAIL_MODE"] = mode
    os.environ["POSTED_LIMIT"] = posted_limit

    return subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True
    )

if run_btn or refresh_btn:

    data["searches"] += 1
    save_data(data)

    if run_btn and os.path.exists(CACHE_FILE):
        results = json.load(open(CACHE_FILE))
    else:
        result = run_backend()

        try:
            match = re.search(r"\[.*\]", result.stdout, re.DOTALL)
            results = json.loads(match.group(0)) if match else []
        except:
            st.error("Parsing failed")
            results = []

        json.dump(results, open(CACHE_FILE, "w"))

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

st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
