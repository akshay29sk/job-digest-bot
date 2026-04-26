import requests
import os
import re
import time

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

SEARCH_QUERY = os.getenv("SEARCH_QUERY")

if not SEARCH_QUERY:
    raise Exception("❌ SEARCH_QUERY is missing. Set it in GitHub Variables.")

ACTOR_ID = "harvestapi~linkedin-post-search"


def fetch_posts():
    print("📌 SEARCH QUERY (raw):", SEARCH_QUERY)

    queries = [q.strip() for q in SEARCH_QUERY.split(",") if q.strip()]
    print("🔎 Parsed queries:", queries)

    run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"

    # ✅ MATCHES YOUR APIFY JSON
    payload = {
        "searchQueries": queries,
        "maxPosts": 100,
        "postedLimit": "24h",
        "sortBy": "date",
        "scrapeComments": False,
        "scrapeReactions": False,
        "postNestedComments": False,
        "postNestedReactions": False
    }

    print("\n➡️ Running Apify actor...")

    run = requests.post(run_url, json=payload).json()

    if "data" not in run:
        print("❌ Run Error:", run)
        return []

    run_data = run["data"]
    run_id = run_data["id"]
    dataset_id = run_data["defaultDatasetId"]

    # ⏳ wait for completion
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"

    for _ in range(24):
        status = requests.get(status_url).json()
        state = status["data"]["status"]
        print("⏳ Status:", state)

        if state == "SUCCEEDED":
            break
        if state in ["FAILED", "ABORTED"]:
            print("❌ Run failed")
            return []

        time.sleep(5)

    # small buffer
    time.sleep(3)

    # ✅ CORRECT DATASET FETCH
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&token={APIFY_TOKEN}"
    posts = requests.get(dataset_url).json()

    print(f"📦 Fetched {len(posts)} posts")
    if posts:
        print("🧪 Sample post:", posts[0])

    return posts


def filter_posts(posts):
    results = []
    seen = set()

    for post in posts:
        text = (post.get("text") or post.get("content") or "").lower()
        link = post.get("url") or post.get("postUrl")

        if not text or not link:
            continue

        # Role filter
        if not any(x in text for x in ["business analyst", "product owner"]):
            continue

        # Hiring intent filter
        if not any(x in text for x in [
            "hiring", "looking", "opening",
            "immediate joiner", "urgent",
            "send resume", "share cv"
        ]):
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
--------------------
"""

    return msg


if __name__ == "__main__":
    try:
        print("🔐 APIFY TOKEN:", APIFY_TOKEN)

        posts = fetch_posts()
        posts = posts[:50]  # performance limit

        filtered = filter_posts(posts)
        msg = build_message(filtered)

        print("\n📨 Final Message:\n", msg)
        send(msg)

    except Exception as e:
        print("❌ Error:", e)
