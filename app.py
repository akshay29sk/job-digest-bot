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
search = st.text_input("🔎 Search Query (Required)", "hiring business analyst")

roles = st.text_input(
    "🎯 Role Keywords (Optional)",
    "",
    help="Leave empty to search all roles"
)

# ==============================
# 📍 LOCATION
# ==============================
location_options = ["india", "pune", "mumbai", "bangalore", "hyderabad", "remote"]

selected_locations = st.multiselect(
    "📍 Location",
    location_options,
    default=[]
)

location
