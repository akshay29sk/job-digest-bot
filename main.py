print("API KEY:", OPENAI_API_KEY)
import requests
import os
import re
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# 🔗 Fetch LinkedIn Jobs + Posts via Google (Improved)
def fetch_jobs():
    url = 'https://www.google.com/search?q=site:linkedin.com+"hiring"+"business+analyst"+OR+"product+owner"+india&num=30'

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    jobs = []

    for g in soup.select("div.g"):
        link_tag = g.find("a")
        title_tag = g.find("h3")
        snippet = g.get_text()

        if link_tag and title_tag:
            link = link_tag.get("href")

            if "linkedin.com" in link:
                jobs.append({
                    "title": title_tag.text.strip(),
                    "desc": snippet,
                    "link": link
                })

    return jobs[:20]


# 🧠 AI Filter (Safe + Strict)
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
- Generic analyst roles

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


# 🧠 Extract recruiter name (basic heuristic)
def extract_recruiter(text):
    words = text.split()
    for i, w in enumerate(words):
        if w.lower() in ["by", "from"]:
            if i + 2 < len(words):
                return words[i+1] + " " + words[i+2]
    return "Not found"


# 📊 Build Digest
def build_digest(jobs):
    results = []

    for job in jobs:
        text = job["desc"].lower()

        # 🎯 Role filter
        if not any(x in text for x in ["business analyst", "product owner"]):
            continue

        # ❌ Reject noise
        if any(x in text for x in ["product manager", "intern", "fresher"]):
            continue

        ai_result = ai_filter(job["desc"])

        try:
            score = int(ai_result.split()[1])
        except:
            score = 50

        # 🔥 Boost hiring intent
        if any(x in text for x in ["hiring", "looking for", "urgent", "opening"]):
            score += 15

        # 📧 Email detection
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", job["desc"])
        email = emails[0] if emails else "Not found"

        # 👤 Recruiter detection
        recruiter = extract_recruiter(job["desc"])

        # 💬 Auto DM message
        dm = f"Hi {recruiter}, came across your hiring post. My experience aligns with Product Owner / Business Analyst roles in Agile environments. Would love to connect."

        if score >= 60:
            results.append((score, job, ai_result, email, recruiter, dm))

    results.sort(reverse=True, key=lambda x: x[0])
    top = results[:5]

    if not top:
        return "📊 No strong LinkedIn matches today."

    msg = "📊 LINKEDIN DAILY DIGEST (PO / BA)\n\n"

    for i, (score, job, reason, email, recruiter, dm) in enumerate(top, 1):
        msg += f"""🔥 {i}. {job['title']}
{reason}

👤 Recruiter: {recruiter}
📧 Email: {email}

💬 Suggested DM:
{dm}

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
