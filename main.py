import requests
import os
import re
import time

# 🔐 ENV LOADER
def get_env(name, required=True, default=None):
    val = os.getenv(name)
    if not val:
        if required and default is None:
            raise Exception(f"{name} missing")
        return default
    return val

TOKEN = get_env("TELEGRAM_TOKEN")
CHAT_ID = get_env("CHAT_ID")
APIFY_TOKEN = get_env("APIFY_TOKEN")

SEARCH_QUERY = get_env("SEARCH_QUERY")
ROLE_KEYWORDS = get_env("ROLE_KEYWORDS")
HIRING_KEYWORDS = get_env("HIRING_KEYWORDS")
LOCATION_KEYWORDS = get_env("LOCATION_KEYWORDS", required=False, default="global")
POSTED_LIMIT = get_env("POSTED_LIMIT")
MAX_POSTS = int(get_env("MAX_POSTS"))
RESULT_LIMIT = int(get_env("RESULT_LIMIT", required=False, default="10"))
EMAIL_MODE = get_env("EMAIL_MODE", required=False, default="prefer_email").lower()

ACTOR_ID = "harvestapi~linkedin-post-search"


# 🚀 FETCH
def fetch_posts():
    queries = [q.strip() for q in SEARCH_QUERY.split(",") if q.strip()]
    print("🔎 Queries:", queries)

    payload = {
        "searchQueries": queries,
        "maxPosts": MAX_POSTS,
        "postedLimit": POSTED_LIMIT,
        "sortBy": "date",
        "scrapeComments": False,
        "scrapeReactions": False
    }

    run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
    run = requests.post(run_url, json=payload).json()

    if "data" not in run:
        print("❌ Run error:", run)
        return []

    run_id = run["data"]["id"]
    dataset_id = run["data"]["defaultDatasetId"]

    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"

    for _ in range(24):
        state = requests.get(status_url).json()["data"]["status"]
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


# 🎯 FILTER
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

        # ❌ spam filter
        if any(x in combined for x in [
            "freshers", "comment interested", "like and share",
            "tag someone", "walk-in", "bulk hiring", "refer someone"
        ]):
            continue

        # 🎯 role
        if not any(x in combined for x in role_words):
            continue

        # 🔥 hiring
        if not any(x in combined for x in hiring_words):
            continue

        # 🌍 location
        if LOCATION_KEYWORDS.lower() != "global":
            if not any(x in combined for x in location_words):
                continue

        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        has_email = len(emails) > 0
        email = emails[0] if has_email else "Not found"

        # 🎯 EMAIL MODE
        if EMAIL_MODE == "only_email" and not has_email:
            continue
        if EMAIL_MODE == "no_email" and has_email:
            continue

        if link in seen:
            continue

        seen.add(link)

        results.append({
            "email": email,
            "link": link,
            "has_email": has_email
        })

    print(f"✅ After filtering: {len(results)} (mode={EMAIL_MODE})")

    if EMAIL_MODE == "prefer_email":
        results.sort(key=lambda x: not x["has_email"])

    return results[:RESULT_LIMIT]


# 📩 TELEGRAM (CHUNKED)
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    chunks = [msg[i:i+3500] for i in range(0, len(msg), 3500)]

    for chunk in chunks:
        payload = {"chat_id": CHAT_ID, "text": chunk}
        res = requests.post(url, data=payload)
        print("📩 Telegram:", res.text)


# 🧾 MESSAGE
def build_message(results):
    if not results:
        return f"📭 No results today\n\n🔎 Query: {SEARCH_QUERY}"

    msg = f"🔥 LINKEDIN POSTS\n🔎 Query: {SEARCH_QUERY}\n\n"

    for i, r in enumerate(results, 1):
        msg += f"{i}\n📧 {r['email']}\n🔗 {r['link']}\n\n"

    return msg


# ▶️ RUN
if __name__ == "__main__":
    posts = fetch_posts()
    filtered = filter_posts(posts)
    msg = build_message(filtered)

    print(msg)
    send(msg)
