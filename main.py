import requests
import os
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 🔍 Fetch real jobs from Indeed
def fetch_jobs():
    url = "https://in.indeed.com/jobs?q=product+owner+business+analyst&l=India"
    
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    jobs = []

    for card in soup.select(".job_seen_beacon")[:20]:
        title = card.select_one("h2")
        link = card.select_one("a")

        if title and link:
            job_title = title.text.strip()
            job_link = "https://in.indeed.com" + link.get("href")

            jobs.append({
                "title": job_title,
                "desc": job_title,
                "link": job_link
            })

    return jobs


# 🎯 Filter rules (YOUR STRATEGY)
def is_valid(job):
    text = (job["title"] + job["desc"]).lower()

    if "product manager" in text:
        return False

    if not ("product owner" in text or "business analyst" in text):
        return False

    if "intern" in text or "fresher" in text:
        return False

    return True


# 🧠 Scoring
def score(job):
    text = (job["title"] + job["desc"]).lower()
    score = 0

    keywords = [
        "agile", "scrum", "backlog",
        "stakeholder", "b2b", "saas",
        "platform", "uat"
    ]

    for k in keywords:
        if k in text:
            score += 1

    return score


# 📊 Build digest
def build_digest(jobs):
    valid = []

    for job in jobs:
        if is_valid(job):
            s = score(job)
            if s >= 2:
                valid.append((s, job))

    valid.sort(reverse=True, key=lambda x: x[0])
    top = valid[:5]

    if not top:
        return "📊 No strong matches today. Will try again tomorrow."

    msg = "📊 DAILY JOB DIGEST (PO / BA)\n\n"

    for i, (s, job) in enumerate(top, 1):
        msg += f"""{i}. {job['title']}
Score: {s}
🔗 {job['link']}

"""

    return msg


# 📩 Send to Telegram
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 🚀 Run
if __name__ == "__main__":
    jobs = fetch_jobs()
    msg = build_digest(jobs)
    send(msg)
