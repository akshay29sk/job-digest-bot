import requests
import os
import re

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


# 🔗 Fetch LinkedIn posts via SerpAPI (NO BLOCKING)
def fetch_posts():
    url = "https://serpapi.com/search.json"

    params = {
        "q": 'site:linkedin.com "hiring" "business analyst" OR "product owner"',
        "api_key": SERPAPI_KEY,
        "num": 20
    }

    res = requests.get(url, params=params)
    data = res.json()

    posts = []

    for result in data.get("organic_results", []):
        link = result.get("link")
        snippet = result.get("snippet", "")
        title = result.get("title", "")

        if "linkedin.com" in link:
            posts.append({
                "title": title,
                "desc": snippet,
                "link": link
            })

    print("Posts fetched:", len(posts))
    return posts


# 📧 Extract only posts with emails
def filter_posts(posts):
    results = []

    for post in posts:
        text = post["desc"].lower()

        if not any(x in text for x in ["business analyst", "product owner"]):
            continue

        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", post["desc"])

        if emails:
            results.append({
                "title": post["title"],
                "email": emails[0],
                "link": post["link"]
            })

    return results[:5]


# 📩 Send to Telegram
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 🚀 Run
if __name__ == "__main__":
    try:
        posts = fetch_posts()
        filtered = filter_posts(posts)

        if not filtered:
            send("📭 No email-based hiring posts found today.")
        else:
            msg = "🔥 LINKEDIN HIRING POSTS (WITH EMAIL)\n\n"

            for i, p in enumerate(filtered, 1):
                msg += f"""{i}. {p['title']}
📧 {p['email']}
🔗 {p['link']}

"""

            send(msg)

    except Exception as e:
        print("Error:", e)
