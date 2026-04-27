# =====================================
# LinkedIn Hiring Radar
# Version: v1.1.0-ui-enhanced
# Status: CLEAN UI + SEARCH TRACKING
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json
import time
import uuid

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
# SETTINGS
# ==============================
mode = st.selectbox(
    "📧 Email Mode",
    ["prefer_email", "only_email", "both", "no_email"]
)

limit = 20

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
    token = st.secrets.get("TELEGRAM_BOT_TOKEN")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        st.error("❌ Telegram secrets missing")
        st.stop()

    return subprocess.run(
        [
            sys.executable,
            "main.py",
            search,
            posted,
            mode,
            str(limit),
            location_str,
            token,
            chat_id,
        ],
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

    start_time = time.time()
    search_id = str(uuid.uuid4())[:8]

    # CACHE
    if run_btn and os.path.exists(CACHE_FILE):
        st.info("⚡ Loading cached results...")
        results = json.load(open(CACHE_FILE))
    else:
        with st.spinner("🚀 Fetching jobs from LinkedIn..."):
            result = run_backend()

        with st.expander("🧪 Debug Info", expanded=False):
            st.write("STDOUT:", result.stdout[:300])
            st.write("STDERR:", result.stderr[:300])

        try:
            results = json.loads(result.stdout.strip()) if result.stdout.strip() else []
        except:
            st.error("❌ Parsing failed")
            results = []

        if results:
            json.dump(results, open(CACHE_FILE, "w"))

    end_time = time.time()
    duration = round(end_time - start_time, 2)

    # ==============================
    # SUMMARY
    # ==============================
    st.success(f"✅ Fetched {len(results)} results in {duration} sec | Search ID: {search_id}")

    # ==============================
    # LOGGING
    # ==============================
    LOG_FILE = "search_logs.json"

    log_entry = {
        "search_id": search_id,
        "query": search,
        "posted": posted,
        "location": location_str,
        "mode": mode,
        "results_count": len(results),
        "time_taken": duration,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if os.path.exists(LOG_FILE):
        logs = json.load(open(LOG_FILE))
    else:
        logs = []

    logs.append(log_entry)
    json.dump(logs, open(LOG_FILE, "w"))

    # ==============================
    # RESULTS
    # ==============================
    st.markdown("## 🎯 Results")

    if not results:
        st.warning("⚠️ No results found")
    else:
        for i, r in enumerate(results, 1):
            st.markdown("---")

            score = r.get("score", 0)
            semantic = r.get("semantic_score", 0)

            if score > 0.7:
                match = "🔥 High Match"
            elif score > 0.5:
                match = "👍 Good Match"
            else:
                match = "➖ Low Match"

            # ✅ Single-line compact header
            st.markdown(f"**{i}. ⭐ {score} | 🧠 {semantic} | {match}**")

            # Email
            if r.get("email") != "Not found":
                st.success(r["email"])
            else:
                st.caption("No Email")

            # Content
            st.write(r.get("content", "")[:300])

            # Link
            st.markdown(f"[🔗 Open Post]({r.get('link')})")

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
