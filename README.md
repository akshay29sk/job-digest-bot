# 🔥 LinkedIn Hiring Radar

> Find high-intent hiring posts (with recruiter emails) faster than LinkedIn feed 🚀

---

## 🚀 Version 0.1.0

### 🎯 What is this?

LinkedIn Hiring Radar is a lightweight tool that helps job seekers discover real hiring posts on LinkedIn—especially those where recruiters are actively asking for resumes or sharing emails.

Instead of scrolling endlessly, this tool surfaces actionable opportunities.

---

## ✨ Features

### 🔍 Smart Search
- Multi-query expansion (e.g., hiring → looking for → job opening)
- Better coverage than single keyword search

### 🧠 Intelligent Filtering
- Filters only actual hiring posts
- Removes noise (generic or non-hiring content)
- Supports:
  - Role keywords
  - Location filters
  - Posted time (1h / 24h / week / month)

### 📧 Email Extraction
- Automatically extracts recruiter emails from posts
- Modes:
  - prefer_email
  - only_email
  - both
  - no_email

### ⭐ Ranking System
Prioritizes:
- Posts with emails
- Urgent hiring signals
- “Apply / Send CV” intent

### 🖥 UI (Streamlit)
- Clean and simple interface
- Shows:
  - Email
  - Post preview
  - Direct LinkedIn link
  - Score (ranking)

### ⚡ Cache + Refresh
- Cached runs → fast & free
- Refresh → fetch latest data (API call)

### 📩 Telegram Alerts
- Sends top hiring leads directly to Telegram

### 📊 Analytics
- Tracks:
  - Visits
  - Searches

---

## 🏗 Architecture

text Streamlit UI    ↓ Environment Variables    ↓ main.py (Core Engine)    ↓ Apify LinkedIn Scraper    ↓ Filtering + Scoring    ↓ JSON Output    ↓ UI + Telegram Alerts 

---

## ⚙️ Setup

### 1. Clone repo

bash git clone https://github.com/your-username/job-digest-bot.git cd job-digest-bot 

---

### 2. Install dependencies

bash pip install -r requirements.txt 

---

### 3. Add environment variables

Create .env or use Streamlit secrets:

env APIFY_TOKEN=your_apify_token TELEGRAM_TOKEN=your_telegram_bot_token CHAT_ID=your_chat_id 

---

### 4. Run app

bash streamlit run app.py 

---

## 🧪 Example Usage

text Search: hiring customer success Location: india, remote Posted: 24h Mode: prefer_email 

👉 Output:
- Top hiring posts
- Recruiter emails
- Direct apply links

---

## ⚠️ Limitations (v0.1.0)

- Advanced filters are UI-only (not applied in backend yet)
- Analytics stored locally (may reset on cloud)
- No company/recruiter extraction yet
- No authentication / multi-user support

---

## 🎯 Who is this for?

- Job seekers who want direct recruiter access
- People tired of LinkedIn noise
- Anyone optimizing for speed + relevance

---

## 🧠 Philosophy

> Speed + Relevance > Volume

Focus:
- Real hiring intent
- Actionable leads
- Minimal noise

---

## 🔮 Roadmap (v0.2.0)

- AI-based ranking
- Recruiter & company extraction
- Query insights (which search matched)
- Persistent analytics (DB)
- Saved searches & alerts

---

## 🏷 Version

text v0.1.0 — Stable MVP 

---

## 🙌 Contributing

Feel free to fork, improve, and suggest features.

---

## ⭐ If you like this

Give it a star ⭐ — helps visibility!

--
