import requests
import os
import re
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 🔗 Fetch LinkedIn hiring posts via Google
def fetch_posts():
    url = "https://www.google.com/search?q=site:linkedin.com+\"hiring\"+\"business+analyst\"+OR+\"product+owner\"+email&num=30"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print("Failed to fetch Google")
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    posts = []

    for g in soup.find_all("div"):
        link_tag = g.find("a", href=True)
        title_tag = g.find("h3")

        if link_tag and title_tag:
            link = link_tag["href"]
            text = g.get_text()

            # Only LinkedIn posts
            if "linkedin.com/posts" in link:
                posts.append({
                    "title": title_tag.text.strip(),
                    "desc": text,
                    "link": link
                })

    print("Posts fetched:", len(posts))
    return posts[:25]


# 📊 Extract only HIGH VALUE posts (email present)
def filter_posts(posts):
    results = []

    for post in posts:
        text = post["desc"].lower()

        # Must contain role
        if not any(x in text for x in ["business analyst", "product owner"]):
            continue

        # Must be hiring signal
        if not any(x in text for x in ["hiring", "looking for", "opening"]):
            continue

        # Extract email
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
            msg = "🔥 HIGH VALUE LINKEDIN POSTS (WITH EMAIL)\n\n"

            for i, p in enumerate(filtered, 1):
                msg += f"""{i}. {p['title']}
📧 {p['email']}
🔗 {p['link']}

"""

            send(msg)

    except Exception as e:
        print("Error:", e)
