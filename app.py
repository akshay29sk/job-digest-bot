import streamlit as st
import subprocess
import os
import json
from datetime import datetime

# 🔐 Load secrets into env
for key, value in st.secrets.items():
    os.environ[key] = value

st.set_page_config(page_title="LinkedIn Hiring Finder", layout="wide")

# ==============================
# 📊 SIMPLE ANALYTICS (FILE BASED)
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
st.title("🔥 LinkedIn Hiring Finder")

st.markdown("""
### 🚀 What this app does
- Finds latest LinkedIn hiring posts
- Extracts recruiter emails (if available)
- Filters based on role & hiring intent
- Helps you apply faster than others

### 💡 Tips to use
1. Prefer **email posts** → faster response
2. Apply within **1–2 hours**
3. Customize query for niche roles
4. Try different combinations daily
""")

# ==============================
# 🎯 PREDEFINED OPTIONS
# ==============================
PREDEFINED_SEARCH = {
    "Business Analyst": "hiring business analyst",
    "Product Owner": "hiring product owner",
    "Urgent Hiring": "urgent hiring business analyst",
    "Custom": ""
}

PREDEFINED_ROLES = {
    "Standard": "business analyst, product owner",
    "Extended": "business analyst, analyst, ba, product owner",
    "Custom": ""
}

col1, col2 = st.columns(2)

with col1:
    search_type = st.selectbox("Search Type", list(PREDEFINED_SEARCH.keys()))
    search = st.text_input("Search Query", PREDEFINED_SEARCH[search_type])

with col2:
    role_type = st.selectbox("Role Type", list(PREDEFINED_ROLES.keys()))
    roles = st.text_input("Role Keywords", PREDEFINED_ROLES[role_type])

# ==============================
# ⚙️ SETTINGS
# ==============================
mode = st.selectbox("Email Mode", ["prefer_email", "only_email", "both", "no_email"])

# FIXED RESULT LIMIT
RESULT_LIMIT = 20

# ==============================
# 🚀 RUN
# ==============================
if st.button("🚀 Run Search"):

    data["searches"] += 1
    save_data(data)

    with st.spinner("Fetching jobs..."):

        os.environ["SEARCH_QUERY"] = search
        os.environ["ROLE_KEYWORDS"] = roles
        os.environ["EMAIL_MODE"] = mode
        os.environ["RESULT_LIMIT"] = str(RESULT_LIMIT)
        os.environ["LOCATION_KEYWORDS"] = "global"

        output = subprocess.getoutput("python3 main.py")

    st.success("Done!")

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
    # 📦 DISPLAY RESULTS
    # ==============================
    st.subheader(f"Results ({len(results)})")

    if not results:
        st.warning("No results found")
    else:
        for i, (email, link) in enumerate(results, 1):
            with st.container():
                st.markdown(f"### {i}")

                colA, colB = st.columns([2, 5])

                with colA:
                    if email != "Not found":
                        st.code(email)
                    else:
                        st.caption("No Email")

                with colB:
                    st.markdown(f"[🔗 Open Post]({link})")

                st.divider()

# ==============================
# 📊 FOOTER ANALYTICS
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
