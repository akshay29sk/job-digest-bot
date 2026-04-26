import streamlit as st
import subprocess
import os
import re

st.set_page_config(page_title="LinkedIn Hiring Finder", layout="wide")

st.title("🔥 LinkedIn Hiring Finder")

# --- INPUTS ---
col1, col2 = st.columns(2)

with col1:
    search = st.text_input("Search Query", "hiring business analyst")
    roles = st.text_input("Role Keywords", "business analyst, product owner")

with col2:
    mode = st.selectbox("Email Mode", ["prefer_email", "only_email", "both", "no_email"])
    limit = st.slider("Results", 5, 20, 10)

# --- RUN ---
if st.button("🚀 Run Search"):

    with st.spinner("Fetching jobs..."):

        # Set env vars
        os.environ["SEARCH_QUERY"] = search
        os.environ["ROLE_KEYWORDS"] = roles
        os.environ["EMAIL_MODE"] = mode
        os.environ["RESULT_LIMIT"] = str(limit)

        # Run script
        output = subprocess.getoutput("python main.py")

    st.success("Done!")

    # --- PARSE OUTPUT ---
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

    # --- DISPLAY ---
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
