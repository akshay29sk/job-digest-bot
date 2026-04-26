import streamlit as st
import subprocess
import os
import json
import sys

for key, value in st.secrets.items():
    os.environ[key] = value

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

# ==============================
# INPUTS
# ==============================
search = st.text_input("🔎 Search Query", "hiring business analyst")
roles = st.text_input("🎯 Role Keywords (Optional)", "")

posted_limit = st.selectbox(
    "🕒 Posted Within",
    ["any", "1h", "24h", "week", "month"],
    index=2
)

mode = st.selectbox("📧 Email Mode", ["prefer_email", "only_email", "both", "no_email"])

# ==============================
# RUN BACKEND
# ==============================
def run_backend():
    os.environ["SEARCH_QUERY"] = search
    os.environ["ROLE_KEYWORDS"] = roles
    os.environ["EMAIL_MODE"] = mode
    os.environ["POSTED_LIMIT"] = posted_limit

    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True
    )

    return result.stdout

# ==============================
# EXECUTE
# ==============================
if st.button("🚀 Run Search"):
    output = run_backend()

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

    st.subheader(f"Results ({len(results)})")

    for i, r in enumerate(results, 1):
        st.markdown("---")

        if r["has_email"]:
            st.success(r["email"])
        else:
            st.caption("No Email")

        if r["content"]:
            st.write(r["content"])

        st.markdown(f"[🔗 Open Post]({r['link']})")
