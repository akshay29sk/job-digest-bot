import requests
import os
import re
import time

def get_env(name, default=None):
    val = os.getenv(name)
    return val if val else default

SEARCH_QUERY = get_env("SEARCH_QUERY")
if not SEARCH_QUERY:
    raise Exception("SEARCH_QUERY is required")

TOKEN = get_env("TELEGRAM_TOKEN")
CHAT_ID = get_env("CHAT_ID")
APIFY_TOKEN = get_env("APIFY_TOKEN")

ROLE_KEYWORDS = get_env("ROLE_KEYWORDS", "")
HIRING_KEYWORDS = get_env("HIRING_KEYWORDS", "")
LOCATION_KEYWORDS = get_env("LOCATION_KEYWORDS", "global")

POSTED_LIMIT = get_env("POSTED_LIMIT", "24h")
MAX_POSTS = int(get_env("MAX_POSTS", "50"))
RESULT_LIMIT = int(get_env("RESULT_LIMIT", "20"))
EMAIL_MODE = get_env("EMAIL_MODE", "prefer_email").lower()

ACTOR_ID = "harvestapi~linkedin-post-search"

# ==============================
# FETCH
# ==============================
def fetch_posts():
    payload = {
        "maxPosts": MAX_POSTS,
        "searchQueries": [SEARCH_QUERY],
        "postedLimit": POSTED_LIMIT,
        "sortBy": "date"
    }

    run = requests.post(
        f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
        json=payload
    ).json()

    if "data" not in run:
        print("❌ Run error:", run)
        return []

    run_id = run["data"]["id"]

    for _ in range(30):
        status = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
        ).json()

        state = status["data"]["status"]

        if state == "SUCCEEDED":
            dataset_id = status["data"]["defaultDatasetId"]
            break

        if state in ["FAILED", "ABORTED"]:
            return []

        time.sleep(5)

    posts = requests.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&token={APIFY_TOKEN}"
    ).json()

    return posts

# ==============================
# FILTER
# ==============================
def filter_posts(posts):
    results = []
    seen = set()

    role_words = [x.strip().lower() for x in ROLE_KEYWORDS.split(",") if x.strip()]
    hiring_words = [x.strip().lower() for x in HIRING_KEYWORDS.split(",") if x.strip()]
    location_words = [x.strip().lower() for x in LOCATION_KEYWORDS.split(",") if x.strip()]

    for post in posts:
        text = (post.get("content") or "").lower()
        raw_content = (post.get("content") or "").strip()
        link = post.get("linkedinUrl")

        if not text or not link:
            continue

        if role_words and not any(x in text for x in role_words):
            continue

        if hiring_words and not any(x in text for x in hiring_words):
            continue

        if LOCATION_KEYWORDS.lower() != "global" and location_words:
            if not any(x in text for x in location_words):
                continue

        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        has_email = len(emails) > 0
        email = emails[0] if has_email else "Not found"

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
            "content": raw_content,
            "has_email": has_email
        })

    if EMAIL_MODE == "prefer_email":
        results.sort(key=lambda x: not x["has_email"])

    return results[:RESULT_LIMIT]

# ==============================
# MESSAGE
# ==============================
def build_message(results):
    if not results:
        return f"📭 No results today\n\n🔎 Query: {SEARCH_QUERY}"

    msg = f"🔥 LINKEDIN POSTS\n🔎 Query: {SEARCH_QUERY}\n\n"

    for i, r in enumerate(results, 1):
        preview = r["content"][:200].replace("\n", " ")
        msg += f"{i}\n📧 {r['email']}\n📝 {preview}\n🔗 {r['link']}\n\n"

    return msg

# ==============================
# TELEGRAM
# ==============================
def send(msg):
    if not TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    posts = fetch_posts()
    filtered = filter_posts(posts)
    msg = build_message(filtered)

    print(msg)
    send(msg)
