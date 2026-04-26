import requests
import os
import re

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

# ✅ Use Apify Actor
ACTOR_ID = "harvestapi~linkedin-post-search"


# 🔥 Multiple simple queries (works MUCH better than complex query)
QUERIES = [
    "hiring business analyst",
    "business analyst immediate joiner",
    "hiring product owner",
    "product owner agile hiring",
    "business analyst jobs india"
]


# 🚀 Fetch posts from Apify
def fetch_posts():
    all_posts = []

    for q in QUERIES:
        print("Running query:", q)

        url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items?token={APIFY_TOKEN}"

        payload = {
            "search": q,
            "maxItems": 10
        }

        res = requests.post(url, json=payload)

        if res.status_code != 200:
            print("Apify Error:", res.text)
            continue

        posts = res.json()
        print(f"Fetched {len(posts)} posts for query: {q}")

        all_posts.extend(posts)

    print("Total posts fetched:", len(all_posts))
    return all_posts


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

        # Extract emails
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


# 📩 Send message to Telegram
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 🧾 Build Telegram message
def build_message(results):
    if not results:
        return "📭 No high-value hiring posts with emails found today."

    msg = "🔥 LINKEDIN HIRING POSTS (EMAIL FOUND)\n\n"

    for i, r in enumerate(results, 1):
        msg += f"""{i}.
📧 {r['email']}
🔗 {r['link']}

"""

    return msg


# ▶️ Main runner
if __name__ == "__main__":
    try:
        print("APIFY TOKEN:", APIFY_TOKEN)

        posts = fetch_posts()
        filtered = filter_posts(posts)
        msg = build_message(filtered)

        print(msg)
        send(msg)

    except Exception as e:
        print("Error:", e)
