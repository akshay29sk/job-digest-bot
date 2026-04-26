import requests
import os
import re

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

ACTOR_ID = "harvestapi/linkedin-post-search"


# 🚀 Run Apify Actor
def fetch_posts():
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"

    payload = {
        "search": "hiring business analyst OR product owner email immediate joiner",
        "maxItems": 20
    }

    res = requests.post(url, json=payload)
    data = res.json()

    run_id = data["data"]["id"]

    dataset_url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}"

    posts = requests.get(dataset_url).json()

    print("Posts fetched:", len(posts))
    return posts


# 🎯 Filter high-value posts
def filter_posts(posts):
    results = []
    seen_links = set()

    for post in posts:
        text = (post.get("text") or "").lower()
        link = post.get("url")

        if not text or not link:
            continue

        # Role filter
        if not any(x in text for x in ["business analyst", "product owner"]):
            continue

        # Hiring intent
        if not any(x in text for x in ["hiring", "looking", "opening"]):
            continue

        # Email extraction
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

        if not emails:
            continue

        # Remove duplicates
        if link in seen_links:
            continue

        seen_links.add(link)

        results.append({
            "email": emails[0],
            "link": link
        })

    return results[:5]


# 📩 Send to Telegram
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 🧾 Build message
def build_message(results):
    if not results:
        return "📭 No high-value hiring posts with emails today."

    msg = "🔥 HIGH VALUE LINKEDIN HIRING POSTS\n\n"

    for i, r in enumerate(results, 1):
        msg += f"""{i}.
📧 {r['email']}
🔗 {r['link']}

"""

    return msg


# ▶️ Run
if __name__ == "__main__":
    try:
        posts = fetch_posts()
        filtered = filter_posts(posts)
        msg = build_message(filtered)

        print(msg)
        send(msg)

    except Exception as e:
        print("Error:", e)
