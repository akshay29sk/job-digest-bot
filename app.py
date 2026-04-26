import streamlit as st
import subprocess
import os
import json

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
# 🎯 PREDEFINED INPUTS
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

mode = st.selectbox("Email Mode", ["prefer_email", "only_email", "both", "no_email"])

RESULT_LIMIT = 20

# ==============================
# 🚀 RUN
# ==============================
if st.button("🚀 Run Search"):

    data["searches"] += 1
    save_data(data)

    with st.spinner("Fetching jobs..."):

        os
