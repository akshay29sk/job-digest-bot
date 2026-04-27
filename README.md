# 🔥 LinkedIn Hiring Radar

A smart job discovery tool that fetches hiring posts from LinkedIn, ranks them using semantic similarity, and presents high-quality leads in a clean UI.

---

## 🚀 What This App Does

- 🔎 Searches LinkedIn posts for hiring-related content
- 🧠 Uses AI (Sentence Transformers) to rank relevance
- 📧 Extracts recruiter emails when available
- 🎯 Filters noise (non-hiring posts)
- 📊 Scores and ranks results
- ⚡ Provides cached + fresh search modes
- 🧾 Tracks search history and performance

---

## 🧱 Architecture Overview

Streamlit UI (app.py)         ↓ Backend Execution (main.py)         ↓ Apify LinkedIn Scraper API         ↓ Processing + Scoring (AI Model)         ↓ Results → UI + Cache + Logs

---

## 📁 Project Structure

├── app.py              # Streamlit frontend (UI + controls) ├── main.py             # Backend logic (fetch + process) ├── analytics.json      # Tracks visits & searches ├── search_logs.json    # Stores search metadata ├── cache_*.json        # Cached search results └── README.md           # Documentation

---

## ⚙️ Environment Variables / Secrets

Set these in Streamlit Secrets or environment:

APIFY_TOKEN=your_apify_token TELEGRAM_BOT_TOKEN=your_bot_token   # (optional, currently unused in UI)

---

## 🧠 Core Logic Explained

### 1. Query Generation

From input role (e.g. product owner), app generates:

hiring product owner product owner job product owner opening looking for product owner

---

### 2. Data Fetching (Apify)

Uses:

Actor: harvestapi~linkedin-post-search

Fetches:
- Post content
- LinkedIn URL
- Metadata

---

### 3. Filtering Logic

#### ✅ Allowed (Hiring intent)

- "we are hiring"
- "looking for"
- "job opening"
- "apply now"
- "send resume"

#### ❌ Removed (Noise)

- "hot take"
- "lessons"
- "opinion"
- "story"
- generic BA/PM advice posts

---

### 4. AI Scoring

Uses:

SentenceTransformer("all-MiniLM-L6-v2")

For each post:

similarity = cosine(query, post)

---

### 5. Final Score Calculation

score = semantic_similarity       + 0.3 (if email found)       + 0.2 (if "apply" present)

---

### 6. Result Buckets

- Primary → Strong hiring intent
- Fallback → Weak intent but still useful

---

## 🎯 UI Features

### 🔍 Inputs

- Role (search query)
- Posted time filter
- Location filter
- Email mode
- Max results

---

### ⚡ Actions

| Button | Action |
|------|--------|
| Run Search | Uses cached results |
| Refresh | Fetches fresh data |

---

### 📊 Output

Each result shows:

Index Score ⭐ Semantic 🧠 Match Level (High / Good / Low) Email (if available) Content preview Link to post

---

## 💾 Caching System

- Cache key based on:
    role + location + posted + mode + limit  
- Stored as:
    cache_<key>.json  
- Reduces API calls and improves speed

---

## 🧾 Search Logging

Each search is logged:

json {   "search_id": "abc123",   "query": "product owner",   "results_count": 18,   "time_taken": 4.2,   "timestamp": "2026-04-27" } 

---

## 📊 Analytics

Tracks:

- Total visits
- Total searches

Stored in:

analytics.json

---

## 🔄 Execution Flow

User clicks search → Backend runs (main.py) → Fetch posts from Apify → Filter + score → Store in session + cache → Render results

---

## 🧠 Key Design Decisions

### 1. Session State (Important)

Streamlit reruns entire script on every interaction.

Fix:
st.session_state["results"]

Prevents results from disappearing on button clicks.

---

### 2. Strict Hiring Filter

Avoids spam like:

- motivational posts
- educational content
- opinion threads

---

### 3. Semantic Threshold

Minimum similarity = 0.05

Ensures relevance without losing good results.

---

## ⚠️ Known Limitations

### LinkedIn Data

- Depends on Apify scraping
- Limited by API quotas
- Not real-time

---

### AI Model

- Lightweight model (fast but not perfect)
- May include borderline posts

---

### Telegram (Currently Disabled in UI)

Telegram integration works but is hidden due to:

- Chat ID complexity
- Bot permission issues
- UX clarity

---

## 📡 Telegram (Future Use)

### Requirements

- Bot created via BotFather
- Privacy mode disabled
- Group converted to supergroup
- Chat ID format:

-100XXXXXXXXXX

---

### Why it was hidden

To avoid:

❌ user confusion ❌ setup failures ❌ inconsistent delivery

---

## 🧪 Debugging

Use built-in debug panel:

STDOUT → backend output STDERR → logs/errors

---

## 🚀 Performance

Typical:

Fetch time: 3–8 seconds Results: 10–50 posts

---

## 📌 Future Improvements

- ✅ Send only HIGH MATCH jobs
- ✅ Deduplicate Telegram messages
- ⏳ Auto-scheduled job alerts
- ⏳ Save user preferences
- ⏳ Export results (CSV)
- ⏳ Multi-role search

---

## 👨‍💻 Tech Stack

- Python
- Streamlit
- Sentence Transformers
- Apify API
- Requests

---

## 🎯 Summary

This app acts as a:

AI-powered LinkedIn job radar

Helping you:

- Cut through noise
- Find real hiring posts
- Reach recruiters faster

---

## 💡 Final Note

The system is now:

✔ Stable ✔ Accurate ✔ Scalable ✔ Ready for enhancements

---

Author: Akshay  
Version: v1.2.x Stable Bu
