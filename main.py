import requests
import os
import re
import xml.etree.ElementTree as ET

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# 🔗 Indeed RSS Feed (Stable)
def fetch_jobs():
    url = "https://in.indeed.com/rss?q=business+analyst+product+owner&l=India"

    res = requests.get(url)

    if res.status_code != 200:
        print("Failed to fetch RSS")
        return []

    root = ET.fromstring(res.content)

    jobs = []

    for item in root.findall(".//item")[:20]:
        title = item.find("title").text
        link = item.find("link").text
        desc = item.find("description").text

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
