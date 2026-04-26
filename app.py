import streamlit as st
import subprocess
import os
import json
import sys

# 🔐 Load secrets
for key, value in st.secrets.items():
    os.environ[key] = value

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

# ==============================
# 📊 ANALYTICS
# ==============================
DATA_FILE = "analytics.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"visits": 0, "searches": 0}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()
data["visits"] += 1
save_data(data)

# ==============================
# 🎯 HEADER
# ==============================
st.markdown("""
# 🔥 LinkedIn Hiring Radar  
### Find recruiter emails faster than others 🚀
""")

# ==============================
# 🎯 BASIC INPUTS
# ==============================
col1, col2 = st.columns(2)

with col1:
    search = st.text_input("Search Query", "hiring business analyst")

with col2:
    roles = st.text_input("Role Keywords", "business analyst, product owner")

# ==============================
# 📍 LOCATION
# ==============================
location_options = ["india", "pune", "mumbai", "bangalore", "hyderabad", "remote"]

selected_locations = st.multiselect(
    "📍 Location",
    location_options,
    default=["india"]
)

location_str = ", ".join(selected_locations) if selected_locations else "global"

# ==============================
# 💼 JOB FILTERS (NEW)
# ==============================
st.markdown("### 💼 Job Filters")

col3, col4, col5 = st.columns(3)

with col3:
    experience = st.multiselect(
        "Experience",
        ["entry", "fresher", "junior", "mid", "senior", "lead"]
    )

with col4:
    job_type = st.multiselect(
        "Job Type",
        ["full-time", "contract", "internship", "freelance"]
    )

with col5:
    work_mode = st.multiselect(
        "Work Mode",
        ["remote", "hybrid", "onsite"]
    )

urgency = st.checkbox("⚡ Urgent Hiring Only")

mode = st.selectbox("Email Mode", ["prefer_email", "only_email", "both", "no_email"])

RESULT_LIMIT = 20

# cache key
cache_key = f"{search}_{location_str}".replace(" ", "_").replace(",", "_")
CACHE_FILE = f"cache_{cache_key}.txt"

# ==============================
# 🚀 BUTTONS
# ==============================
colA, colB = st.columns(2)
run_search = colA.button("🚀 Run Search (Use Cache)")
refresh = colB.button("🔄 Refresh (Costs API)")

# ==============================
# 🧠 FETCH
# ==============================
if run_search or refresh:

    data["searches"] += 1
    save_data(data)

    use_cache = run_search and os.path.exists(CACHE_FILE)

    with st.spinner("Fetching jobs..."):

        if use_cache:
            with open(CACHE_FILE, "r") as f:
                output = f.read()
            st.success("⚡ Loaded from cache")
        else:
            os.environ["SEARCH_QUERY"] = search
            os.environ["ROLE_KEYWORDS"] = roles
            os.environ["HIRING_KEYWORDS"] = "hiring, urgent, immediate joiner"
            os.environ["EMAIL_MODE"] = mode
            os.environ["RESULT_LIMIT"] = str(RESULT_LIMIT)
            os.environ["LOCATION_KEYWORDS"] = "global"
            os.environ["MAX_POSTS"] = "30"
            os.environ["POSTED_LIMIT"] = "24h"

            result = subprocess.run(
                [sys.executable, "main.py"],
                capture_output=True,
                text=True
            )

            output = result.stdout + "\n\nERROR:\n" + result.stderr

            with open(CACHE_FILE, "w") as f:
                f.write(output)

            st.success("✅ Fresh data fetched")

    # ==============================
    # 📊 PARSE
    # ==============================
    results = []
    lines = output.split("\n")

    email = None
    link = None

    for line in lines:
        if "📧" in line:
            email = line.replace("📧", "").strip()
        if "🔗" in line:
            link = line.replace("🔗", "").strip()
            if email and link:
                results.append({
                    "email": email,
                    "link": link,
                    "text": link.lower(),
                    "has_email": email != "Not found"
                })
                email, link = None, None

    # ==============================
    # 🧠 FILTER + SCORING
    # ==============================
    for r in results:
        score = 0
        text = r["text"]

        # Location match
        if any(loc in text for loc in selected_locations):
            score += 2
            r["location_match"] = True

        # Experience
        if experience and any(x in text for x in experience):
            score += 1

        # Job type
        if job_type and any(x in text for x in job_type):
            score += 1

        # Work mode
        if work_mode and any(x in text for x in work_mode):
            score += 1

        # Urgency
        if urgency and any(x in text for x in ["urgent", "immediate"]):
            score += 2

        # Email priority
        if r["has_email"]:
            score += 2

        r["score"] = score

    # sort by score
    results.sort(key=lambda x: -x["score"])

    # ==============================
    # 📦 DISPLAY
    # ==============================
    st.markdown("---")
    st.subheader(f"🎯 Results ({len(results)})")

    if not results:
        st.warning("No results found")
    else:
        for i, r in enumerate(results[:RESULT_LIMIT], 1):

            with st.container():
                st.markdown("---")

                col1, col2 = st.columns([1, 6])

                with col1:
                    st.markdown(f"**#{i}**")

                with col2:
                    if r["has_email"]:
                        st.success(r["email"])
                    else:
                        st.caption("No Email")

                    st.markdown(f"[🔗 Open Post]({r['link']})")
