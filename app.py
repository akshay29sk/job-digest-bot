# =====================================
# LinkedIn Hiring Radar
# Version: v1.0.1-ui-patch
# Status: STABLE UI (Indent Fix + Metric Fix)
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json

# ==============================
# LOAD SECRETS
# ==============================
for k, v in st.secrets.items():
    os.environ[k] = v

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

# ==============================
# ANALYTICS
# ==============================
DATA_FILE = "analytics.json"

if not os.path.exists(DATA_FILE):
    json.dump({"visits": 0, "searches": 0}, open(DATA_FILE, "w"))

data = json.load(open(DATA_FILE))
data["visits"] += 1
json.dump(data, open(DATA_FILE, "w"))

# ==============================
# HEADER
# ==============================
st.title("🔥 LinkedIn Hiring Radar")

# ==============================
# INPUTS
# ==============================
search = st.text_input("🔎 Role", "product owner")

posted = st.selectbox(
    "🕒 Posted",
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
use_filters = st.toggle("⚙️ Advanced Filters")

limit = 20

if use_filters:
    st.markdown("### 💼 Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.multiselect("Experience", ["entry", "junior", "mid", "senior", "lead"])

    with col2:
        st.multiselect("Job Type", ["full-time", "contract", "internship"])

    with col3:
        st.multiselect("Work Mode", ["remote", "hybrid", "onsite"])

    st.checkbox("⚡ Urgent Hiring Only")

    limit = st.selectbox("📊 Results Count", [10, 20, 50], index=1)

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
cache_key = f"{search}_{location_str}_{posted}_{mode}_{limit}".replace(" ", "_")
CACHE_FILE = f"cache_{cache_key}.json"

# ==============================
# BUTTONS
# ==============================
col1, col2 = st.columns(2)

run_btn = col1.button("🚀 Run Search (Cached)")
refresh_btn = col2.button("🔄 Refresh (API Call)")

# ==============================
# BACKEND
# ==============================
def run_backend():
    os.environ["SEARCH_QUERY"] = search
    os.environ["POSTED_LIMIT"] = posted
    os.environ["EMAIL_MODE"] = mode
    os.environ["RESULT_LIMIT"] = str(limit)
    os.environ["LOCATION_KEYWORDS"] = location_str

    return subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True
    )

# ==============================
# EXECUTION
# ==============================
trigger = run_btn or refresh_btn

if trigger:

    if not search.strip():
        st.error("Role is required")
        st.stop()

    data["searches"] += 1
    json.dump(data, open(DATA_FILE, "w"))

    # CACHE
    if run_btn and os.path.exists(CACHE_FILE):
        st.info("⚡ Loading cached results...")
        results = json.load(open(CACHE_FILE))

    else:
        with st.spinner("🚀 Fetching jobs from LinkedIn..."):
            result = run_backend()

        # DEBUG (SAFE)
        with st.expander("🧪 Debug Info", expanded=False):
            st.write("Button Triggered:", trigger)
            st.write("STDOUT:", result.stdout[:500])
            st.write("STDERR:", result.stderr[:500])

        try:
            results = json.loads(result.stdout.strip()) if result.stdout.strip() else []
        except:
            st.error("❌ Parsing failed")
            results = []

        # ✅ FIXED INDENTATION HERE
        if results:
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

            col1, col2 = st.columns(2)

            with col1:
                st.metric("⭐ Score", r.get("score"))

            with col2:  # ✅ FIXED (was col1 earlier)
                st.metric("🧠 Semantic", r.get("semantic_score"))

            if r.get("score", 0) > 0.7:
                st.success("🔥 High Match")
            elif r.get("score", 0) > 0.5:
                st.info("👍 Good Match")

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
