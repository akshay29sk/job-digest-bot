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
    queries = [q.strip() for q in SEARCH_QUERY.split(",") if q.strip()]

    print("📌 SEARCH QUERY (raw):", SEARCH_QUERY)
    print("🔎 Parsed queries:", queries)

    all_posts = []

    for q in queries:
        print("\n➡️ Running query:", q)

        run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"

        payload = {
            "queries": [q],
            "maxItems": 20
        }

        run = requests.post(run_url, json=payload).json()

        if "data" not in run:
            print("❌ Run Error:", run)
            continue

        run_data = run["data"]
        run_id = run_data["id"]
        dataset_id = run_data["defaultDatasetId"]

        # ⏳ Wait for completion
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"

        for _ in range(24):  # ~2 mins max
            status = requests.get(status_url).json()
            state = status["data"]["status"]
            print("⏳ Status:", state)

            if state == "SUCCEEDED":
                break
            if state in ["FAILED", "ABORTED"]:
                print("❌ Run failed")
                break

            time.sleep(5)

        # ⏳ Ensure dataset ready
        time.sleep(3)

        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&token={APIFY_TOKEN}"
        posts = requests.get(dataset_url).json()

        print(f"📦 Fetched {len(posts)} posts for query: {q}")

        # 👇 Debug sample (first run visibility)
        if posts:
            print("🧪 Sample post:", posts[0])

        all_posts.extend(posts)

    print("\n📊 Total posts fetched:", len(all_posts))
    return all_posts


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

        # Hiring intent filter (improved)
        if not any(x in text for x in [
            "hiring", "looking", "opening",
            "immediate joiner", "urgent",
            "send resume", "share cv"
        ]):
            continue

        # Email extraction (not strict)
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

        # Limit dataset for performance
        posts = posts[:50]

        filtered = filter_posts(posts)
        msg = build_message(filtered)

        print("\n📨 Final Message:\n", msg)
        send(msg)

    except Exception as e:
        print("❌ Error:", e)
