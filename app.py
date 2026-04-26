# =====================================
# LinkedIn Hiring Radar
# Version: v0.2.7
# File: app.py
# =====================================

import streamlit as st
import subprocess, os, sys, json

# Load secrets
for k,v in st.secrets.items():
    os.environ[k]=v

st.set_page_config(page_title="LinkedIn Hiring Radar", layout="wide")

# ==============================
# ANALYTICS
# ==============================
file="analytics.json"
if not os.path.exists(file):
    json.dump({"visits":0,"searches":0},open(file,"w"))

data=json.load(open(file))
data["visits"]+=1
json.dump(data,open(file,"w"))

# ==============================
# HEADER
# ==============================
st.title("🔥 LinkedIn Hiring Radar")

# ==============================
# INPUTS
# ==============================
search=st.text_input("🔎 Role","product owner")

posted=st.selectbox("🕒 Posted",["any","1h","24h","week","month"],index=2)

loc=st.multiselect("📍 Location",["india","pune","mumbai","remote"])

mode=st.selectbox("📧 Email Mode",["prefer_email","only_email","both","no_email"])

use_filters=st.toggle("⚙️ Advanced Filters")

limit=20
if use_filters:
    st.markdown("### Filters")
    st.multiselect("Experience",["entry","mid","senior"])
    st.multiselect("Work Mode",["remote","onsite","hybrid"])
    st.checkbox("⚡ Urgent Only")
    limit=st.selectbox("Results Count",[10,20,50],index=1)

# ==============================
# CACHE
# ==============================
key=f"{search}_{posted}_{mode}_{limit}"
cache=f"cache_{key}.json"

# ==============================
# BUTTONS
# ==============================
c1,c2=st.columns(2)
run=c1.button("🚀 Run Search (Cached)")
refresh=c2.button("🔄 Refresh (API Call)")

def call():
    os.environ["SEARCH_QUERY"]=search
    os.environ["POSTED_LIMIT"]=posted
    os.environ["EMAIL_MODE"]=mode
    os.environ["RESULT_LIMIT"]=str(limit)

    return subprocess.run([sys.executable,"main.py"],capture_output=True,text=True)

# ==============================
# EXECUTION
# ==============================
if run or refresh:

    data["searches"]+=1
    json.dump(data,open(file,"w"))

    if run and os.path.exists(cache):
    st.info("⚡ Loading cached results...")
    results = json.load(open(cache))
    else:
with st.spinner("🚀 Fetching jobs from LinkedIn..."):
    res = call()

        with st.expander("🧪 Debug"):
            st.write("STDOUT:",res.stdout[:300])
            st.write("STDERR:",res.stderr[:300])

        try:
            results=json.loads(res.stdout.strip())
        except:
            results=[]

        json.dump(results,open(cache,"w"))
        st.success("✅ Fresh data fetched")

    st.markdown("## 🎯 Results")

    if not results:
        st.warning("No results found")
    else:
        for r in results:
            st.markdown("---")
            st.caption(f"{r['score']} | {r['semantic_score']}")

            if r["email"]!="Not found":
                st.success(r["email"])

            st.write(r["content"][:300])
            st.markdown(r["link"])

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption(f"👀 Visits: {data['visits']} | 🔍 Searches: {data['searches']}")
