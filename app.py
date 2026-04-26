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
# 🎯 INPUTS
# ==============================
col1, col2 = st.columns(2)

with col1:
    search = st.text_input("Search Query", "hiring business analyst")

with col2:
    roles = st.text_input("Role Keywords", "business analyst, product owner")

# 📍 LOCATION FILTER (NEW)
location = st.selectbox(
    "📍 Location",
    [
        "global",
        "india",
        "pune",
        "mumbai",
        "bangalore",
        "hyderabad",
        "remote",
        "india, remote"
    ]
)

mode = st.selectbox("Email Mode", ["prefer_email", "only_email", "both", "no_email"])

RESULT_LIMIT = 20

# Cache file
CACHE_FILE = f"cache_{search.replace(' ', '_')}_{location.replace(',', '_')}.txt"

# ==============================
# 🚀 BUTTONS
# ==============================
colA, colB = st.columns(2)

run_search = colA.button("🚀 Run Search (Use Cache)")
refresh = colB.button("🔄 Refresh (Costs API)")

# ==============================
# 🧠 FETCH LOGIC
# ==============================
if run_search or refresh:

    data["searches"] += 1
    save_data(data)

    use_cache = run_search and os.path.exists(CACHE_FILE)

    with st.spinner("Fetching jobs..."):

        if use_cache:
            with open(CACHE_FILE, "r") as f:
                output = f.read()
            st.success("⚡ Loaded from cache (no cost)")
        else:
            os.environ["SEARCH_QUERY"] = search
            os.environ["ROLE_KEYWORDS"] = roles
            os.environ["HIRING_KEYWORDS"] = "hiring, looking, urgent, immediate joiner, send resume, share cv"
            os.environ["EMAIL_MODE"] = mode
            os.environ["RESULT_LIMIT"] = str(RESULT_LIMIT)
            os.environ["LOCATION_KEYWORDS"] = location   # ✅ DYNAMIC
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
    # 📊 PARSE OUTPUT
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
                results.append((email, link))
                email, link = None, None

    # ==============================
    # 📦 DISPLAY
    # ==============================
    st.markdown("---")
    st.subheader(f"🎯 Results ({len(results)})")

    emails_count = sum(1 for r in results if r[0] != "Not found")
    st.info(f"📧 {emails_count} posts with emails out of {len(results)}")

    if not results:
        st.warning("No results found → try different location/query")
    else:
        for i, (email, link) in enumerate(results, 1):

            has_email = email != "Not found"

            with st.container():
                st.markdown("---")

                col1, col2 = st.columns([1, 6])

                with col1:
                    st.markdown(f"""
                    <div style="
                        background:#1f2937;
                        color:white;
                        border-radius:10px;
                        text-align:center;
                        padding:12px;
                        font-weight:bold;
                    ">
                        #{i}
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    if has_email:
                        st.markdown("🟢 **Email Found**")
                        st.text_input("", email, key=f"email_{i}")
                    else:
                        st.markdown("🔴 *No Email Available*")

                    st.markdown(f"""
                    🔗 <a href="{link}" target="_blank">Open LinkedIn Post</a>
                    """, unsafe_allow_html=True)

# ==============================
# 📊 FOOTER
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
