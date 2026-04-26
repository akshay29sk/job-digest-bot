# =====================================
# LinkedIn Hiring Radar
# Version: v0.2.4
# File: app.py
# =====================================

import streamlit as st
import subprocess
import os
import sys
import json
import re

for k, v in st.secrets.items():
    os.environ[k] = v

st.set_page_config(page_title="Hiring Radar", layout="wide")

# Analytics
file = "analytics.json"
if not os.path.exists(file):
    json.dump({"visits":0,"searches":0}, open(file,"w"))

data = json.load(open(file))
data["visits"] += 1
json.dump(data, open(file,"w"))

st.title("🔥 LinkedIn Hiring Radar")

search = st.text_input("🔎 Role", "product owner")

posted = st.selectbox("🕒 Posted", ["any","1h","24h","week","month"], index=2)

locs = st.multiselect("📍 Location", ["india","pune","mumbai","remote"])

mode = st.selectbox("📧 Email Mode", ["prefer_email","only_email","both","no_email"])

use_filters = st.toggle("⚙️ Advanced Filters")

limit = 20
if use_filters:
    limit = st.selectbox("Results", [10,20,50])

key = f"{search}_{posted}_{mode}_{limit}"
cache = f"cache_{key}.json"

c1,c2 = st.columns(2)
run = c1.button("Run")
refresh = c2.button("Refresh")

def call():
    os.environ["SEARCH_QUERY"]=search
    os.environ["POSTED_LIMIT"]=posted
    os.environ["EMAIL_MODE"]=mode
    os.environ["RESULT_LIMIT"]=str(limit)
    return subprocess.run([sys.executable,"main.py"],capture_output=True,text=True)

if run or refresh:

    data["searches"] += 1
    json.dump(data, open(file,"w"))

    if run and os.path.exists(cache):
        results = json.load(open(cache))
    else:
        r = call()

        match = re.search(r"\[.*\]", r.stdout, re.DOTALL)
        results = json.loads(match.group(0)) if match else []

        json.dump(results, open(cache,"w"))

    st.markdown("## Results")

    if not results:
        st.warning("No results")
    else:
        for x in results:
            st.markdown("---")
            st.caption(f"{x['score']} | {x['semantic_score']}")
            if x["email"]!="Not found":
                st.success(x["email"])
            st.write(x["content"][:300])
            st.markdown(x["link"])

st.markdown("---")
st.caption(f"Visits: {data['visits']} | Searches: {data['searches']}")
