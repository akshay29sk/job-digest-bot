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
search = st.text_input("🔎 Search Query (Required)", "hiring business analyst")

roles = st.text_input(
    "🎯 Role Keywords (Optional)",
    "",
    help="Leave empty to search all roles"
)

# 🕒 Posted filter
posted_limit = st.selectbox(
    "🕒 Posted Within",
    ["any", "1h", "24h", "week", "month", "3months", "6months", "year"],
    index=2
)

# 📍 Location
location_options = ["india", "pune", "mumbai", "bangalore", "hyderabad", "remote"]

selected_locations = st.multiselect(
    "📍 Location",
    location_options,
    default=[]
)

location_str = ", ".join(selected_locations) if selected_locations else "global"

# ==============================
# ⚙️ ADVANCED FILTERS
# ==============================
use_filters = st.toggle("⚙️ Enable Advanced Filters")

result_limit_ui = 20

if use_filters:
    st.markdown("### 💼 Job Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.multiselect("Experience", ["entry", "fresher", "junior", "mid", "senior", "lead"])

    with col2:
        st.multiselect("Job Type", ["full-time", "contract", "internship", "freelance"])

    with col3:
        st.multiselect("Work Mode", ["remote", "hybrid", "onsite"])

    st.checkbox("⚡ Urgent Hiring Only")

    result_limit_ui = st.selectbox(
        "📊 Number of Results",
        [10, 20, 50],
        index=1
    )

# ==============================
# ⚙️ OTHER SETTINGS
# ==============================
mode = st.selectbox(
    "📧 Email Mode",
    ["prefer_email", "only_email", "both", "no_email"]
)

# ==============================
# 🧠 CACHE
# ==============================
cache_key = f"{search}_{location_str}_{posted_limit}".replace(" ", "_").replace(",", "_")
CACHE_FILE = f"cache_{cache_key}.txt"

# ==============================
# 🚀 BUTTONS
# ==============================
colA, colB = st.columns(2)
run_search = colA.button("🚀 Run Search (Use Cache)")
refresh = colB.button("🔄 Refresh (Costs API)")

# ==============================
# 🧠 BACKEND RUNNER
# ==============================
def run_backend(search, roles, location_str, mode, result_limit_ui, posted_limit):
    os.environ["SEARCH_QUERY"] = search
    os.environ["ROLE_KEYWORDS"] = roles
    os.environ["HIRING_KEYWORDS"] = "hiring, looking, urgent, opportunity"
    os.environ["EMAIL_MODE"] = mode
    os.environ["RESULT_LIMIT"] = str(result_limit_ui)
    os.environ["LOCATION_KEYWORDS"] = location_str
    os.environ["POSTED_LIMIT"] = posted_limit
    os.environ["MAX_POSTS"] = "50"

    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True
    )

    return result.stdout + "\n\nERROR:\n" + result.stderr

# ==============================
# 🧠 FETCH
# ==============================
if run_search or refresh:

    if not search.strip():
        st.error("Search Query is required")
        st.stop()

    data["searches"] += 1
    save_data(data)

    use_cache_flag = run_search and os.path.exists(CACHE_FILE)

    with st.spinner("Fetching jobs..."):

        if use_cache_flag:
            with open(CACHE_FILE, "r") as f:
                output = f.read()
            st.success("⚡ Loaded from cache")

        else:
            output = run_backend(search, roles, location_str, mode, result_limit_ui, posted_limit)

            if "No results today" in output and posted_limit == "24h":
                st.warning("⚠️ No results in 24h → expanding to week")
                output = run_backend(search, roles, location_str, mode, result_limit_ui, "week")
                posted_limit = "week"

            with open(CACHE_FILE, "w") as f:
                f.write(output)

            st.success(f"✅ Data fetched ({posted_limit})")

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
                    "has_email": email != "Not found",
                    "is_fresh": posted_limit in ["1h", "24h"]
                })
                email, link = None, None

    # ==============================
    # ⭐ BEST LEADS
    # ==============================
    best_leads = [r for r in results if r["has_email"]][:5]

    if best_leads:
        st.markdown("## ⭐ Best Leads (Apply First)")

        for i, r in enumerate(best_leads, 1):
            st.success(f"{i}. {r['email']}")
            st.markdown(f"[🔗 Open Post]({r['link']})")

        st.markdown("---")

    # ==============================
    # 📦 DISPLAY
    # ==============================
    st.markdown("---")
    st.subheader(f"🎯 Results ({len(results)})")
    st.caption(f"🕒 Showing results from: {posted_limit}")

    email_count = sum(1 for r in results if r["has_email"])
    st.info(f"📧 {email_count} posts with emails")

    if not results:
        st.warning("No results found → try broader filters")
    else:
        for i, r in enumerate(results, 1):

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
                    badges = []

                    if r["has_email"]:
                        badges.append("📧 Email")
                    if r["is_fresh"]:
                        badges.append("🔥 Fresh")

                    if badges:
                        st.markdown(" ".join(badges))

                    if r["has_email"]:
                        st.success(r["email"])
                    else:
                        st.caption("❌ No Email")

                    st.markdown(f"[🔗 Open Post]({r['link']})")

# ==============================
# 📊 FOOTER
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
