import requests
import os
import re
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# 🔗 Fetch jobs from Naukri
def fetch_jobs():
    url = "https://www.naukri.com/business-analyst-product-owner-jobs-in-india"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print("Failed to fetch Naukri")
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    jobs = []

    for card in soup.select("article.jobTuple")[:20]:
        title_tag = card.select_one("a.title")
        desc_tag = card.select_one(".job-description")

        if title_tag:
            title = title_tag.text.strip()
            link = title_tag.get("href")
            desc = desc_tag.text if desc_tag else ""

            jobs.append({
                "title": title,
                "desc": desc,
                "link": link
            })

    print("Jobs fetched:", len(jobs))
    return jobs


# 📧 Extract email-based opportunities
def filter_jobs(jobs):
    results = []

    for job in jobs:
        text = (job["title"] + " " + job["desc"]).lower()

        if not any(x in text for x in ["business analyst", "product owner"]):
            continue

        # Extract emails
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", job["desc"])

        if emails:
            results.append({
                "title": job["title"],
                "email": emails[0],
                "link": job["link"]
            })

    return results[:5]


# 📩 Send to Telegram
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 🚀 Run
if __name__ == "__main__":
    try:
        jobs = fetch_jobs()
        filtered = filter_jobs(jobs)

        if not filtered:
            send("📭 No email-based opportunities found today.")
        else:
            msg = "🔥 EMAIL-BASED JOB OPPORTUNITIES\n\n"

            for i, job in enumerate(filtered, 1):
                msg += f"""{i}. {job['title']}
📧 {job['email']}
🔗 {job['link']}

"""

            send(msg)

    except Exception as e:
        print("Error:", e)
