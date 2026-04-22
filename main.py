import requests
import os
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# 🔗 Fetch LinkedIn Jobs (recent)
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


# 🧠 AI Filter (SAFE)
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
            return "Score: 50 Reason: Fallback (API issue)"

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI Exception:", e)
        return "Score: 50 Reason: Exception fallback"


# 📊 Build Digest
def build_digest(jobs):
    results = []

    for job in jobs:
        text = job["title"].lower()

        # ❌ Exclude unwanted roles
        if "product manager" in text:
            continue

        if not ("product owner" in text or "business analyst" in text):
            continue

        ai_result = ai_filter(job["desc"])

        # ✅ Safe score parsing
        try:
            score = int(ai_result.split()[1])
        except:
            score = 50

        if score >= 60:
            results.append((score, job, ai_result))

    results.sort(reverse=True, key=lambda x: x[0])
    top = results[:5]

    if not top:
        return "📊 No strong LinkedIn matches today."

    msg = "📊 LINKEDIN DAILY DIGEST (PO / BA)\n\n"

    for i, (score, job, reason) in enumerate(top, 1):
        msg += f"""{i}. {job['title']}
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
        print("Jobs fetched:", len(jobs))

        msg = build_digest(jobs)
        print("Message:", msg)

        send(msg)

    except Exception as e:
        print("Main Error:", e)
