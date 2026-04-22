import requests
import os

TOKEN = os.getenv("AAHiB1mVtZ_VufnRyj8qRzz4aCdI3ZBu6xE")
CHAT_ID = os.getenv("8393912346")

def fetch_jobs():
    return [
        {
            "title": "Product Owner - SaaS",
            "desc": "Agile Scrum backlog stakeholder B2B platform",
            "link": "https://example.com/job1"
        },
        {
            "title": "Business Analyst - Platform",
            "desc": "UAT stakeholder agile marketplace",
            "link": "https://example.com/job2"
        }
    ]

def is_valid(job):
    text = (job["title"] + job["desc"]).lower()

    if "product manager" in text:
        return False

    if not ("product owner" in text or "business analyst" in text):
        return False

    return True

def score(job):
    text = (job["title"] + job["desc"]).lower()
    score = 0

    keywords = ["agile", "scrum", "backlog", "stakeholder", "b2b", "saas"]

    for k in keywords:
        if k in text:
            score += 1

    return score

def build_digest(jobs):
    valid = []

    for job in jobs:
        if is_valid(job):
            s = score(job)
            if s >= 2:
                valid.append((s, job))

    valid.sort(reverse=True, key=lambda x: x[0])
    top = valid[:5]

    msg = "📊 DAILY JOB DIGEST\n\n"

    for i, (s, job) in enumerate(top, 1):
        msg += f"{i}. {job['title']}\nScore: {s}\n🔗 {job['link']}\n\n"

    return msg

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

if __name__ == "__main__":
    jobs = fetch_jobs()
    msg = build_digest(jobs)
    send(msg)
