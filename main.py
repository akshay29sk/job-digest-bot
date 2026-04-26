import requests
import os
import re

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

# ✅ dynamic query from env OR fallback
SEARCH_QUERY = os.getenv(
    "SEARCH_QUERY",
    "hiring business analyst, hiring product owner, business analyst immediate joiner"
)

ACTOR_ID = "harvestapi~linkedin-post-search"


def fetch_posts():
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    # ✅ IMPORTANT: convert string → list
    queries = [q.strip() for q in SEARCH_QUERY.split(",") if q.strip()]

    payload = {
        "queries": queries,   # 🔥 correct field
        "maxItems": 20
    }

    print("Using queries:", queries)

    res = requests.post(url, json=payload)

    if res.status_code != 200:
        print("Apify Error:", res.text)
        return []

    posts = res.json()

    print("Posts fetched:", len(posts))
    return posts


def filter_posts(posts):
    results = []
    seen = set()

    for post in posts:
        text = (post.get("text") or "").lower()
        link = post.get("url")

        if not text or not link:
            continue

        if not any(x in text for x in ["business analyst", "product owner"]):
            continue

        if not any(x in text for x in ["hiring", "looking", "opening"]):
            continue

        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        email = emails[0] if emails else "Not found"

        if link in seen:
            continue

        seen.add(link)

        results.append({
            "email": email,
            "link": link
        })

    return results[:5]


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def build_message(results):
    if not results:
        return f"📭 No results today.\n\n🔎 Query: {SEARCH_QUERY}"

    msg = f"🔥 LINKEDIN POSTS\n🔎 Query: {SEARCH_QUERY}\n\n"

    for i, r in enumerate(results, 1):
        msg += f"""{i}.
📧 {r['email']}
🔗 {r['link']}

"""

    return msg


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
