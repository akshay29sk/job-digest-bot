# =====================================
# LinkedIn Hiring Radar
# Version: v0.1.5
# File: app.py
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json

# Load secrets
for key, value in st.secrets.items():
    os.environ[key] = value

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

# ==============================
# ANALYTICS
# ==============================
DATA_FILE = "analytics.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"visits": 0, "searches": 0}
    return json.load(open(DATA_FILE))

def save_data(data):
    json.dump(data, open(DATA_FILE, "w"))

data = load_data()
data["visits"] += 1
save_data(data)

# ==============================
# HEADER
# ==============================
st.title("🔥 LinkedIn Hiring Radar")

# ==============================
# INPUTS
# ==============================
search = st.text_input("🔎 Search Query", "hiring customer success manager")

roles = st.text_input("🎯 Role Keywords (Optional)", "")

posted_limit = st.selectbox(
    "🕒 Posted Within",
    ["any", "1h", "24h", "week", "month"],
    index=2
)

# Location
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
        st.multiselect("Experience", ["entry", "junior", "mid", "senior", "lead"])

    with col2:
        st.multiselect("Job Type", ["full-time", "contract", "internship"])

    with col3:
        st.multiselect("Work Mode", ["remote", "hybrid", "onsite"])

    st.checkbox("⚡ Ur
