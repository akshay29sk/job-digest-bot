# =====================================
# LinkedIn Hiring Radar
# Version: v0.2.6
# File: app.py
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json

# Load secrets
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
search = st.text_input("🔎 Role", value="product owner")

posted = st.selectbox("🕒 Posted", ["any", "1h", "24h", "week", "month"], index=2)

locs = st.multiselect("📍 Location", ["india", "pune", "mumbai", "bangalore", "hyderabad", "remote"])
location_str = ", ".join(locs) if locs else "global"

mode = st.selectbox("📧 Email Mode", ["prefer_email", "only_email", "both", "no_email"])

use_filters = st.toggle("⚙️ Advanced Filters")

limit = 20
if use_filters:
    limit = st.selectbox("📊 Results Count", [10, 20, 50], index=1)

# ==============================
# CACHE
# ==============================
key = f"{search}_{posted}_{mode}_{limit}"
cache_file = f"cache_{key}.json"

# ==============================
# BUTTONS
# ==============================
c1, c2 = st.columns(2)
run_btn = c1.button("🚀 Run Search (Cached)")
refresh_btn = c2.button("🔄 Refresh (API Call)")

# ==============================
# BACKEND CALL
# ==============================
def call_backend():
    os.environ["SEARCH_QUERY"] = search
    os.environ["POSTED_LIMIT"] = posted
    os.environ["EMAIL_MODE"] = mode
    os.environ["RESULT_LIMIT"] = str(limit)
    os.environ["LOCATION_KEYWORDS"] = location_str

    return subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True,
    )

# ==============================
# EXECUTION
# ==============================
if run_btn or refresh_btn:

    data["searches"] += 1
    json.dump(data, open(DATA_FILE, "w"))

    # cache
    if run_btn and os.path.exists(cache_file):
        results = json.load(open(cache_file))
        st.success("⚡ Loaded from cache")

    else:
        with st.spinner("Fetching jobs..."):
            res = call_backend()

        # DEBUG PANEL (important)
        with st.expander("🧪 Debug", expanded=False):
            st.write("STDOUT:", res.stdout[:500])
            st.write("STDERR:", res.stderr[:500])

        try:
            results = json.loads(res.stdout.strip())
        except Exception:
            results = []

        json.dump(results, open(cache_file, "w"))
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
            st.caption(f"⭐ {r['score']} | 🧠 {r['semantic_score']}")

            if r["email"] != "Not found":
                st.success(r["email"])
            else:
                st.caption("No Email")

            st.write(r["content"][:400])
            st.markdown(f"[🔗 Open Post]({r['link']})")

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
