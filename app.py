# =====================================
# LinkedIn Hiring Radar
# Version: v1.2.3-ui-hardened
# Status: PRODUCTION READY (SAFE + CLEAN)
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json
import time
import uuid
import hashlib

# ==============================
# LOAD SECRETS
# ==============================
for k, v in st.secrets.items():
    os.environ[k] = v

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

# ==============================
# SESSION INIT
# ==============================
if "results" not in st.session_state:
    st.session_state["results"] = []

# ==============================
# ANALYTICS
# ==============================
DATA_FILE = "analytics.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"visits": 0, "searches": 0}, f)

try:
    with open(DATA_FILE) as f:
        data = json.load(f)
except:
    data = {"visits": 0, "searches": 0}

data["visits"] += 1

with open(DATA_FILE, "w") as f:
    json.dump(data, f)

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

limit = st.selectbox(
    "📊 Max Results",
    [10, 20, 50, 100],
    index=1
)

# ==============================
# CACHE (SAFE KEY)
# ==============================
raw_key = f"{search}_{location_str}_{posted}_{mode}_{limit}"
cache_key = hashlib.md5(raw_key.encode()).hexdigest()
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
    try:
        return subprocess.run(
            [
                sys.executable,
                "main.py",
                search,
                posted,
                mode,
                str(limit),
                location_str,
                "",
                "",
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
    except subprocess.TimeoutExpired:
        st.error("⏳ Backend timeout. Please try again.")
        return None

# ==============================
# EXECUTION
# ==============================
trigger = run_btn or refresh_btn

if trigger:

    if not search.strip():
        st.error("Role is required")
        st.stop()

    data["searches"] += 1
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

    start_time = time.time()
    search_id = str(uuid.uuid4())[:8]

    # ==============================
    # CACHE LOAD
    # ==============================
    if run_btn and os.path.exists(CACHE_FILE):
        st.info("⚡ Loading cached results...")

        try:
            with open(CACHE_FILE) as f:
                results = json.load(f)
        except:
            results = []

        st.session_state["results"] = results

    else:
        with st.spinner("🚀 Fetching jobs from LinkedIn..."):
            result = run_backend()

        if result is None:
            st.stop()

        if result.returncode != 0:
            st.error("❌ Backend failed")
            st.stop()

        with st.expander("🧪 Debug Info", expanded=False):
            st.code(result.stdout[:300])
            st.code(result.stderr[:300])

        try:
            results = json.loads(result.stdout.strip()) if result.stdout.strip() else []
        except:
            st.error("❌ Parsing failed")
            results = []

        st.session_state["results"] = results

        if results:
            with open(CACHE_FILE, "w") as f:
                json.dump(results, f)

    duration = round(time.time() - start_time, 2)

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

    try:
        with open(LOG_FILE) as f:
            logs = json.load(f)
    except:
        logs = []

    logs.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f)

# ==============================
# ALWAYS SHOW RESULTS
# ==============================
results = st.session_state.get("results", [])

st.markdown("## 🎯 Results")

if not results:
    st.warning("⚠️ No results found. Try broader roles like 'product manager' or 'business analyst'")
else:
    st.caption(f"Showing top {len(results)} results")

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

        st.markdown(f"**{i}. ⭐ {score} | 🧠 {semantic} | {match}**")

        if r.get("email") != "Not found":
            st.success(r["email"])
        else:
            st.caption("No Email")

        st.write(r.get("content", "")[:300])
        st.markdown(f"[🔗 Open Post]({r.get('link')})")

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
