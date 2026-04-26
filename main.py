import requests
import os
import re
import time

# 🔐 ENV VARIABLES
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

SEARCH_QUERY = os.getenv("SEARCH_QUERY")
ROLE_KEYWORDS = os.getenv("ROLE_KEYWORDS")
HIRING_KEYWORDS = os.getenv("HIRING_KEYWORDS")
LOCATION_KEYWORDS = os.getenv("LOCATION_KEYWORDS")
POSTED_LIMIT = os.getenv("POSTED_LIMIT")

# ✅ STRICT VALIDATION (NO HARDCODING)
def get_required_env(name):
    val = os.getenv(name)
    if not val:
        raise Exception(f"❌ {name} is missing in GitHub Variables")
    return val

SEARCH_QUERY = get_required_env("SEARCH_QUERY")
ROLE_KEYWORDS = get_required_env("ROLE_KEYWORDS")
HIRING_KEYWORDS = get_required_env("HIRING_KEYWORDS")
LOCATION_KEYWORDS = get_required_env("LOCATION_KEYWORDS")
POSTED_LIMIT = get_required_env("POSTED_LIMIT")

max_posts_env = get_required_env("MAX_POSTS")
MAX_POSTS = int(max_posts_env)

ACTOR_ID = "harvestapi~linkedin-post-search"


def fetch_posts():
    queries = [q.strip() for q in SEARCH_QUERY.split(",") if q.strip()]
    print("🔎 Queries:", queries)

    run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"

    payload = {
        "searchQueries": queries,
        "maxPosts": MAX_POSTS,
        "postedLimit": POSTED_LIMIT,
        "sortBy": "date",
        "scrapeComments": False,
        "scrapeReactions": False
    }

    print("\n➡️ Running Apify actor...")

    run = requests.post(run_url, json=payload).json()

    if "data" not in run:
        print("❌ Run Error:", run)
        return []

    run_id = run["data"]["id"]
    dataset_id = run["data"]["defaultDatasetId"]

    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"

    for _ in range(24):
        status = requests.get(status_url).json()
        state = status["data"]["status"]
        print("⏳ Status:", state)

        if state == "SUCCEEDED":
            break
        if state in ["FAILED", "ABORTED"]:
            return []

        time.sleep(5)

    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&token={APIFY_TOKEN}"
    posts = requests.get(dataset_url).json()

    print("📦 Fetched:", len(posts))
    return posts


def filter_posts(posts):
    results = []
    seen = set()

    role_words = [x.strip().lower() for x in ROLE_KEYWORDS.split(",")]
    hiring_words = [x.strip().lower() for x in HIRING_KEYWORDS.split(",")]
    location_words = [x.strip().lower() for x in LOCATION_KEYWORDS.split(",")]

    for post in posts:
        text = (post.get("content") or "").lower()
        link = post.get("linkedinUrl")
        author_info = (post.get("author", {}).get("info") or "").lower()

        combined = text + " " + author_info

        if not text or not link:
            continue

        if not any(x in combined for x in role_words):
            continue

        if not any(x in combined for x in hiring_words):
            continue

        if not any(x in combined for x in location_words):
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
        return f"📭 No results today\n\n🔎 Query: {SEARCH_QUERY}"

    msg = f"🔥 LINKEDIN POSTS\n🔎 Query: {SEARCH_QUERY}\n\n"

    for i, r in enumerate(results, 1):
        msg += f"{i}\n📧 {r['email']}\n🔗 {r['link']}\n\n"

    return msg


if __name__ == "__main__":
    posts = fetch_posts()
    filtered = filter_posts(posts)
    msg = build_message(filtered)

    print("\n📨 Final Message:\n", msg)
    send(msg)
