
# 🔥 LinkedIn Hiring Bot (Telegram)

Automated system to fetch LinkedIn hiring posts and send curated results to Telegram.

---

## 🚀 Features

- Scrapes latest LinkedIn hiring posts via Apify
- Filters based on role, hiring intent, location
- Extracts emails from posts
- Sends results to Telegram
- Fully configurable via GitHub Variables
- Supports multiple email filtering modes

---

## ⚙️ Setup

### 1. GitHub Secrets

- TELEGRAM_TOKEN
- CHAT_ID
- APIFY_TOKEN

---

### 2. GitHub Variables

| Variable | Description | Example |
|--------|------------|--------|
| SEARCH_QUERY | Search queries | hiring business analyst |
| ROLE_KEYWORDS | Role filter | business analyst, product owner |
| HIRING_KEYWORDS | Hiring intent | hiring, urgent, send resume |
| LOCATION_KEYWORDS | Location filter | india, remote OR global |
| MAX_POSTS | Posts fetched | 100 |
| POSTED_LIMIT | Time filter | 24h |
| RESULT_LIMIT | Output count | 10 |
| EMAIL_MODE | Email logic | only_email / no_email / both / prefer_email |

---

## 🎯 EMAIL_MODE Options

| Mode | Behavior |
|------|--------|
| only_email | Only posts with email |
| no_email | Only posts without email |
| both | All posts |
| prefer_email | Email posts first |

---

## 🧠 How It Works

1. Fetch posts from Apify
2. Apply filters
3. Extract emails
4. Apply EMAIL_MODE
5. Send results to Telegram

---

## 📩 Output Example
