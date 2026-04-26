import streamlit as st
import subprocess
import os
import sys

# Load secrets
for key, value in st.secrets.items():
    os.environ[key] = value

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

# ==============================
# HEADER
# ==============================
st.title("🔥 LinkedIn Hiring Radar")

# ==============================
# INPUTS
# ==============================
search = st.text_input("🔎 Search Query", "hiring business analyst")

roles = st.text_input(
    "🎯 Role Keywords (Optional)",
    "",
    help="Leave empty for broad search"
)

# 🕒 Posted filter
posted_limit = st.selectbox(
    "🕒 Posted Within",
    ["any", "1h", "24h", "week", "month"],
    index=2
)

# 📍 Location
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
        st.multiselect("Experience", ["entry", "fresher", "junior", "mid", "senior", "lead"])

    with col2:
        st.multiselect("Job Type", ["full-time", "contract", "internship", "freelance"])

    with col3:
        st.multiselect("Work Mode", ["remote", "hybrid", "onsite"])

    st.checkbox("⚡ Urgent Hiring Only")

    result_limit = st.selectbox("📊 Number of Results", [10, 20, 50], index=1)

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
cache_key = f"{search}_{roles}_{location_str}_{posted_limit}_{mode}".replace(" ", "_").replace(",", "_")
CACHE_FILE = f"cache_{cache_key}.txt"

# ==============================
# BUTTONS
# ==============================
col1, col2 = st.columns(2)

run_btn = col1.button("🚀 Run Search (Cached)")
refresh_btn = col2.button("🔄 Refresh (Costs API)")

# ==============================
# BACKEND RUNNER
# ==============================
def run_backend():
    os.environ["SEARCH_QUERY"] = search
    os.environ["ROLE_KEYWORDS"] = roles
    os.environ["EMAIL_MODE"] = mode
    os.environ["POSTED_LIMIT"] = posted_limit
    os.environ["LOCATION_KEYWORDS"] = location_str
    os.environ["RESULT_LIMIT"] = str(result_limit)

    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True
    )

    return result.stdout

# ==============================
# EXECUTION
# ==============================
if run_btn or refresh_btn:

    if not search.strip():
        st.error("Search Query is required")
        st.stop()

    # USE CACHE
    if run_btn and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            output = f.read()
        st.success("⚡ Loaded from cache")

    else:
        output = run_backend()

        # Save cache
        with open(CACHE_FILE, "w") as f:
            f.write(output)

        st.success("✅ Fresh data fetched")

    # ==============================
    # PARSE OUTPUT
    # ==============================
    results = []
    lines = output.split("\n")

    email = None
    content = None
    link = None

    for line in lines:
        if "📧" in line:
            email = line.replace("📧", "").strip()

        elif "📝" in line:
            content = line.replace("📝", "").strip()

        elif "🔗" in line:
            link = line.replace("🔗", "").strip()

            if email and link:
                results.append({
                    "email": email,
                    "content": content,
                    "link": link,
                    "has_email": email != "Not found"
                })
                email, content, link = None, None, None

    # ==============================
    # BEST LEADS
    # ==============================
    best = [r for r in results if r["has_email"]][:5]

    if best:
        st.markdown("## ⭐ Best Leads")

        for r in best:
            st.success(r["email"])
            st.markdown(f"[🔗 Open Post]({r['link']})")

    # ==============================
    # RESULTS
    # ==============================
    st.markdown("## 🎯 Results")

    for i, r in enumerate(results, 1):
        st.markdown("---")

        if r["has_email"]:
            st.success(r["email"])
        else:
            st.caption("❌ No Email")

        if r["content"]:
            st.write(r["content"])

        st.markdown(f"[🔗 Open Post]({r['link']})")
