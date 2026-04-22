import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def build_message():
    msg = """🔥 DAILY LINKEDIN HIRING SEARCH

🎯 Business Analyst (Hiring Posts)
https://www.linkedin.com/search/results/content/?keywords=hiring%20business%20analyst&origin=GLOBAL_SEARCH_HEADER&sortBy=%22date_posted%22

🎯 Product Owner (Hiring Posts)
https://www.linkedin.com/search/results/content/?keywords=hiring%20product%20owner&origin=GLOBAL_SEARCH_HEADER&sortBy=%22date_posted%22

🎯 Immediate Joiner / Urgent Hiring
https://www.linkedin.com/search/results/content/?keywords=urgent%20hiring%20business%20analyst&sortBy=%22date_posted%22

💡 Tip:
- Look for posts with emails
- Filter by “Latest”
- Apply within 1–2 hours

"""

    return msg


if __name__ == "__main__":
    msg = build_message()
    send(msg)
