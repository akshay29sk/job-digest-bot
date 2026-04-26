# =====================================
# LinkedIn Hiring Radar
# Version: v0.2.2
# File: app.py
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json
import re

# ==============================
# LOAD SECRETS
# ==============================
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
# HEADER
# ==============================
st.title("🔥 LinkedIn Hiring Radar")

# ==============================
# ROLE INPUT (UPDATED UX)
# ==============================
search = st.text_input(
    "🔎 Role",
    value="product owner",
    placeholder="e.g. product owner, business analyst, product manager"
)

# ==============================
# CORE FILTERS
# ==============================
posted_limit = st.selectbox(
    "🕒 Posted Within",
    ["any", "1h", "24h", "week", "month"],
    index=2
)

# Location
location_options = ["india", "pune", "mumbai", "bangalore", "hyderabad", "remote"]
selected_locations = st.multiselect("📍 Location", location_options)
location_str = ", ".join(selected_locations) if selected_locations else "global"

# ==============================
# ADVANCED FILTERS
# ==============================
use_filters = st.toggle("⚙️ Enable Advanced Filters")

result_limit = 20

if use_filters:
    st.markdown("### 💼 Job Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.multiselect("Experience", ["entry", "junior", "mid", "senior", "lead"])

    with col2:
        st.multiselect("Job Type", ["full-time", "contract", "internship"])

    with col3:
        st.multiselect("Work Mode", ["remote", "hybrid", "onsite"])

    st.checkbox("⚡ Urgent Hiring Only")

    result_limit = st.selectbox("📊 Results Count", [10, 20, 50], index=1)

# ==============================
# SETTINGS
# ==============================
mode = st.selectbox(
    "📧 Email Mode",
    ["prefer_email", "only_email", "both", "no_email"]
)

# ==============================
# CACHE
# ==============================
cache_key = f"{search}_{location_str}_{posted_limit}_{mode}".replace(" ", "_")
CACHE_FILE = f"cache_{cache_key}.json"

# ==============================
# BUTTONS
# ==============================
col1, col2 = st.columns(2)
run_btn = col1.button("🚀 Run Search (Cached)")
refresh_btn = col2.button("🔄 Refresh (API Call)")

# ==============================
# BACKEND CALL
# ==============================
def run_backend():
    os.environ["SEARCH_QUERY"] = search
    os.environ["EMAIL_MODE"] = mode
    os.environ["POSTED_LIMIT"] = posted_limit
    os.environ["LOCATION_KEYWORDS"] = location_str
    os.environ["RESULT_LIMIT"] = str(result_limit)

    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True
    )
    return result

# ==============================
# EXECUTION
# ==============================
if run_btn or refresh_btn:

    if not search.strip():
        st.error("Role is required")
        st.stop()

    data["searches"] += 1
    save_data(data)

    results = []

    # CACHE
    if run_btn and os.path.exists(CACHE_FILE):
        results = json.load(open(CACHE_FILE))
        st.success("⚡ Loaded from cache")

    else:
        with st.spinner("Fetching jobs..."):
            result = run_backend()

        # DEBUG PANEL
        with st.expander("🧪 Debug Info", expanded=False):

            if result.returncode != 0:
                st.error("❌ Backend Error")
                st.text(result.stderr)
            else:
                st.info("✅ Backend executed successfully")

            if result.stdout:
                st.text(result.stdout[:1200])
            else:
                st.warning("No output received")

        # SAFE PARSING
        try:
            match = re.search(r"\[.*\]", result.stdout, re.DOTALL)
            results = json.loads(match.group(0)) if match else []
        except:
            st.error("❌ Parsing failed")
            st.text(result.stdout[:1000])
            st.stop()

        json.dump(results, open(CACHE_FILE, "w"))
        st.success("✅ Fresh data fetched")

    # ==============================
    # RESULTS
    # ==============================
    st.markdown("## 🎯 Results")

    if not results:
        st.warning("⚠️ No results found")
    else:
        for r in results:
            st.markdown("---")

            st.caption(f"⭐ Score: {r.get('score')} | 🧠 Semantic: {r.get('semantic_score')}")

            if r.get("email") != "Not found":
                st.success(r["email"])
            else:
                st.caption("No Email")

            st.write(r.get("content", "")[:400])
            st.markdown(f"[🔗 Open Post]({r.get('link')})")

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
