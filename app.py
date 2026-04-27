# =====================================
# LinkedIn Hiring Radar
# Version: v1.2.1-ui-telegram-fixed
# Status: SESSION FIX + TELEGRAM WORKING
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json
import time
import uuid
import requests

# ==============================
# LOAD SECRETS
# ==============================
for k, v in st.secrets.items():
    os.environ[k] = v

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

# ✅ SESSION INIT
if "results" not in st.session_state:
    st.session_state["results"] = []

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

    if not token:
        st.error("❌ Telegram bot token missing")
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
            "",
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
        st.session_state["results"] = results  # ✅ STORE
    else:
        with st.spinner("🚀 Fetching jobs from LinkedIn..."):
            result = run_backend()

        with st.expander("🧪 Debug Info", expanded=False):
            st.write("STDOUT:", result.stdout[:300])
            st.write("STDERR:", result.stderr[:300])

        try:
            results = json.loads(result.stdout.strip()) if result.stdout.strip() else []
            st.session_state["results"] = results  # ✅ STORE
        except:
            st.error("❌ Parsing failed")
            results = []

        if results:
            json.dump(results, open(CACHE_FILE, "w"))

    duration = round(time.time() - start_time, 2)

    st.success(f"✅ Fetched {len(results)} results in {duration} sec | Search ID: {search_id}")

    # LOGGING
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

    logs = json.load(open(LOG_FILE)) if os.path.exists(LOG_FILE) else []
    logs.append(log_entry)
    json.dump(logs, open(LOG_FILE, "w"))

# ==============================
# ALWAYS SHOW RESULTS (KEY FIX)
# ==============================
results = st.session_state.get("results", [])

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

        st.markdown(f"**{i}. ⭐ {score} | 🧠 {semantic} | {match}**")

        if r.get("email") != "Not found":
            st.success(r["email"])
        else:
            st.caption("No Email")

        st.write(r.get("content", "")[:300])
        st.markdown(f"[🔗 Open Post]({r.get('link')})")

    # ==============================
    # TELEGRAM (NOW WORKS)
    # ==============================
    st.markdown("## 📤 Send to Telegram")

    st.info("👉 Get your chat ID from @userinfobot")

    user_chat_id = st.text_input("📱 Telegram Chat ID")

    if st.button("📨 Send to Telegram"):
        if not user_chat_id.strip():
            st.error("Please enter chat ID")
        else:
            token = st.secrets.get("TELEGRAM_BOT_TOKEN")
            sent = 0

            for r in results[:5]:
                msg = f"""🔥 New Job Lead

📧 {r['email']}
⭐ Score: {r['score']}

{r['content'][:200]}

🔗 {r['link']}"""

                try:
                    requests.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        data={"chat_id": user_chat_id.strip(), "text": msg},
                        timeout=10
                    )
                    sent += 1
                except:
                    pass

            st.success(f"✅ Sent {sent} messages")

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
