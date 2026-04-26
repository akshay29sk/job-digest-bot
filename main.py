import requests
import os
import re
import time

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

SEARCH_QUERY = os.getenv(
    "SEARCH_QUERY",
    "hiring business analyst, hiring product owner, business analyst immediate joiner"
)

ACTOR_ID = "harvestapi~linkedin-post-search"


# 🚀 Run actor (async)
def fetch_posts():
    queries = [q.strip() for q in SEARCH_QUERY.split(",") if q.strip()]
    all_posts = []

    for q in queries:
        print("Running query:", q)

        run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"

        payload = {
            "queries": [q],
            "maxItems": 10
        }

        run = requests.post(run_url, json=payload).json()

        if "data" not in run:
            print("Run Error:", run)
            continue

        run_id = run["data"]["id"]

        # ⏳ Wait for completion
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"

        for _ in range(24):  # max ~2 minutes
            status = requests.get(status_url).json()
            state = status["data"]["status"]

            print("Status:", state)

            if state == "SUCCEEDED":
                break

            if state in ["FAILED", "ABORTED"]:
                print("Run failed")
                break

            time.sleep(5)

        # 📦 Fetch dataset
        dataset_url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}"
        posts = requests.get(dataset_url).json()

        print(f"Fetched {len(posts)} posts for query:", q)
        all_posts.extend(posts)

    print("Total posts fetched:", len(all_posts))
    return all_posts


# 🎯 Filter posts
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


# 📩 Send to Telegram
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 🧾 Build message
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


# ▶️ Main
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
