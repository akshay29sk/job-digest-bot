# =====================================
# LinkedIn Hiring Radar
# Version: v0.1.2
# File: app.py
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json

# Load secrets
for key, value in st.secrets.items():
    os.environ[key] = value

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

# ==============================
# ANALYTICS
# ==============================
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

# ==============================
# UI
# ==============================
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

location_options = ["india", "pune", "mumbai", "bangalore", "hyderabad", "remote"]
selected_locations = st.multiselect("📍 Location", location_options)
location_str = ", ".join(selected_locations) if selected_locations else "global"

cache_file = f"cache_{search}_{posted_limit}_{mode}.json".replace(" ", "_")

# ==============================
# RUN BACKEND
# ==============================
def run_backend():
    os.environ["SEARCH_QUERY"] = search
    os.environ["POSTED_LIMIT"] = posted_limit
    os.environ["EMAIL_MODE"] = mode
    os.environ["LOCATION_KEYWORDS"] = location_str

    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True
    )

    return result.stdout

# ==============================
# EXECUTION
# ==============================
if st.button("🚀 Run Search"):

    data["searches"] += 1
    save_data(data)

    if os.path.exists(cache_file):
        results = json.load(open(cache_file))
        st.success("⚡ Loaded from cache")
    else:
        output = run_backend()

        try:
            results = json.loads(output)
        except:
            st.error("❌ Parsing failed")
            st.text(output)
            st.stop()

        json.dump(results, open(cache_file, "w"))
        st.success("✅ Fresh data fetched")

    # ==============================
    # RESULTS
    # ==============================
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

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
