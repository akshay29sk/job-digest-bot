import requests
import os
import re
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



# 🔗 Fetch jobs from Indeed (RELIABLE)
def fetch_jobs():
    url = "https://in.indeed.com/jobs?q=product+owner+business+analyst&l=India"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print("Failed to fetch Indeed")
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    jobs = []

    for card in soup.select(".job_seen_beacon")[:20]:
        title_tag = card.select_one("h2 a")
        company_tag = card.select_one(".companyName")

        if title_tag:
            title = title_tag.text.strip()
            link = "https://in.indeed.com" + title_tag.get("href")

            company = company_tag.text.strip() if company_tag else "Unknown"

            jobs.append({
                "title": title,
                "desc": title,
                "company": company,
                "link": link
            })

    print("Jobs fetched:", len(jobs))
    return jobs


# 🧠 AI Filter
def ai_filter(job_text):
    url = "https://api.openai.com/v1/chat/completions"

    prompt = f"""
Strictly filter for:
- Product Owner OR Business Analyst
- Agile/Scrum roles
- 5+ years experience

Reject:
- Product Manager
- Fresher/Intern

Return:
Score: number (0-100)
Reason: one line
"""

    try:
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

        data = res.json()

        if "choices" not in data:
            print("OpenAI Error:", data)
            return "Score: 50 Reason: fallback"

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI Exception:", e)
        return "Score: 50 Reason: exception fallback"


# 📊 Build Digest
def build_digest(jobs):
    results = []

    for job in jobs:
        text = job["title"].lower()

        if not any(x in text for x in ["business analyst", "product owner"]):
            continue

        if any(x in text for x in ["product manager", "intern", "fresher"]):
            continue

        ai_result = ai_filter(job["title"])

        try:
            score = int(ai_result.split()[1])
        except:
            score = 50

        if score >= 60:
            results.append((score, job, ai_result))

    results.sort(reverse=True, key=lambda x: x[0])
    top = results[:5]

    if not top:
        return "📊 No strong matches today."

    msg = "📊 DAILY JOB DIGEST (PO / BA)\n\n"

    for i, (score, job, reason) in enumerate(top, 1):
        msg += f"""🔥 {i}. {job['title']}
🏢 {job['company']}
{reason}

🔗 {job['link']}

"""

    return msg


# 📩 Send to Telegram
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram Error:", e)


# 🚀 Run
if __name__ == "__main__":
    try:
        jobs = fetch_jobs()
        msg = build_digest(jobs)
        print("Message:", msg)
        send(msg)
    except Exception as e:
        print("Main Error:", e)
