import streamlit as st
import subprocess
import os
import json
import sys

# 🔐 Load secrets into env
for key, value in st.secrets.items():
    os.environ[key] = value

st.set_page_config(page_title="LinkedIn Hiring Finder", layout="wide")

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
st.title("🔥 LinkedIn Hiring Finder")

st.markdown("""
### 🚀 What this app does
- Finds latest LinkedIn hiring posts
- Extracts recruiter emails
- Helps you apply faster

### 💡 Tips
- Prefer email posts
- Apply within 1–2 hours
- Try multiple queries
""")

# ==============================
# 🎯 INPUTS
# ==============================
search = st.text_input("Search Query", "hiring business analyst")
roles = st.text_input("Role Keywords", "business analyst, product owner")
mode = st.selectbox("Email Mode", ["prefer_email", "only_email", "both", "no_email"])

RESULT_LIMIT = 20

# ==============================
# 🚀 RUN
# ==============================
if st.button("🚀 Run Search"):

    data["searches"] += 1
    save_data(data)

    with st.spinner("Fetching jobs..."):

        # ✅ ENV VARIABLES (ALL REQUIRED)
        os.environ["SEARCH_QUERY"] = search
        os.environ["ROLE_KEYWORDS"] = roles
        os.environ["HIRING_KEYWORDS"] = "hiring, looking, urgent, immediate joiner, send resume, share cv"
        os.environ["EMAIL_MODE"] = "both"  # relaxed for testing
        os.environ["RESULT_LIMIT"] = str(RESULT_LIMIT)
        os.environ["LOCATION_KEYWORDS"] = "global"
        os.environ["MAX_POSTS"] = "100"
        os.environ["POSTED_LIMIT"] = "24h"

        # 🔥 CORRECT EXECUTION
        result = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True
        )

        output = result.stdout + "\n\nERROR:\n" + result.stderr

    st.success("Done!")

    # 🔍 DEBUG INFO
    st.write("Working directory:", os.getcwd())
    st.text_area("RAW OUTPUT", output, height=300)

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
    st.subheader(f"Results ({len(results)})")

    if not results:
        st.warning("No results found → check RAW OUTPUT above")
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
# 📊 FOOTER
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
