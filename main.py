import requests
import os
import re

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

# 🔥 dynamic search query
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "hiring business analyst OR product owner email")

ACTOR_ID = "harvestapi/linkedin-post-search"


# 🚀 Fetch posts
def fetch_posts():
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    payload = {
        "search": SEARCH_QUERY,
        "maxItems": 20
    }

    print("Using search:", SEARCH_QUERY)

    res = requests.post(url, json=payload)

    if res.status_code != 200:
        print("Apify Error:", res.text)
        return []

    posts = res.json()

    print("Posts fetched:", len(posts))
    return posts


# 🎯 Filter posts
def filter_posts(posts):
    results = []
    seen = set()

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

        # Extract emails
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

        if not emails:
            continue

        if link in seen:
            continue

        seen.add(link)

        results.append({
            "email": emails[0],
            "link": link
        })

    return results[:5]


# 📩 Telegram
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 🧾 Message
def build_message(results):
    if not results:
        return f"📭 No results today.\n\n🔎 Query: {SEARCH_QUERY}"

    msg = f"🔥 LINKEDIN HIRING POSTS\n🔎 Query: {SEARCH_QUERY}\n\n"

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
