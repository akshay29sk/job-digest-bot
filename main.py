import requests
import os
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# 🔗 LinkedIn Jobs (recent only)
def fetch_jobs():
    url = "https://www.linkedin.com/jobs/search/?keywords=product%20owner%20business%20analyst&f_TPR=r86400"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    jobs = []

    for card in soup.select(".base-card")[:15]:
        title = card.select_one("h3")
        link = card.select_one("a")

        if title and link:
            jobs.append({
                "title": title.text.strip(),
                "desc": title.text.strip(),
                "link": link.get("href")
            })

    return jobs


# 🎯 AI filter
def ai_filter(job_text):
    url = "https://api.openai.com/v1/chat/completions"

    prompt = f"""
Filter strictly for:
- Product Owner OR Business Analyst
- Agile/Scrum roles
- Mid/Senior level

Reject:
- Product Manager
- Fresher/Intern roles

Return:
Score: number (0-100)
Reason: one line
"""

    res = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": job_text + "\n\n" + prompt}
            ]
        }
    )

    return res.json()["choices"][0]["message"]["content"]


# 📊 Build digest
def build_digest(jobs):
    results = []

    for job in jobs:
        text = job["title"].lower()

        if "product manager" in text:
            continue

        if not ("product owner" in text or "business analyst" in text):
            continue

        ai_result = ai_filter(job["desc"])

        try:
            score = int(ai_result.split()[1])
        except:
            score = 0

        if score >= 70:
            results.append((score, job, ai_result))

    results.sort(reverse=True, key=lambda x: x[0])
    top = results[:5]

    if not top:
        return "📊 No strong LinkedIn matches today."

    msg = "📊 LINKEDIN DAILY DIGEST\n\n"

    for i, (score, job, reason) in enumerate(top, 1):
        msg += f"""{i}. {job['title']}
{reason}
🔗 {job['link']}

"""

    return msg


# 📩 Telegram
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 🚀 Run
if __name__ == "__main__":
    jobs = fetch_jobs()
    msg = build_digest(jobs)
    send(msg)
