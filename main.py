import requests
import os
import re
import time
import json

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
POSTED_LIMIT = get_env("POSTED_LIMIT", "24h")
MAX_POSTS = int(get_env("MAX_POSTS", "50"))
RESULT_LIMIT = int(get_env("RESULT_LIMIT", "20"))
EMAIL_MODE = get_env("EMAIL_MODE", "prefer_email").lower()
LOCATION_KEYWORDS = get_env("LOCATION_KEYWORDS", "global")

ACTOR_ID = "harvestapi~linkedin-post-search"

ROLE_MAP = {
    "customer success": ["customer success manager", "csm"],
    "business analyst": ["ba"],
    "product manager": ["pm", "product owner"]
}

# ==============================
# QUERY GENERATION
# ==============================
def generate_queries(base):
    base = base.lower()
    queries = set()

    queries.add(base)
    queries.add(base.replace("hiring", "looking for"))
    queries.add(base.replace("hiring", "job opening"))

    for key, vals in ROLE_MAP.items():
        if key in base:
            for v in vals:
                queries.add(base.replace(key, v))

    return list(queries)

# ==============================
# FETCH
# ==============================
def fetch_posts():
    all_posts = []
    queries = generate_queries(SEARCH_QUERY)

    for q in queries:
        payload = {
            "maxPosts": max(5, MAX_POSTS // len(queries)),
            "searchQueries": [q],
            "postedLimit": POSTED_LIMIT,
            "sortBy": "date"
        }

        run = requests.post(
            f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
            json=payload
        ).json()

        if "data" not in run:
            continue

        run_id = run["data"]["id"]

        for _ in range(20):
            status = requests.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
            ).json()

            if status["data"]["status"] == "SUCCEEDED":
                dataset_id = status["data"]["defaultDatasetId"]
                break

            time.sleep(3)

        posts = requests.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&token={APIFY_TOKEN}"
        ).json()

        all_posts.extend(posts)

    return all_posts

# ==============================
# PROCESS
# ==============================
def process_posts(posts):
    results = []
    seen = set()

    for post in posts:
        text = (post.get("content") or "").lower()
        raw = (post.get("content") or "").strip()
        link = post.get("linkedinUrl")

        if not text or not link or link in seen:
            continue

        seen.add(link)

        if not any(x in text for x in ["hiring", "looking", "apply", "send cv"]):
            continue

        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        email = emails[0] if emails else "Not found"
        has_email = bool(emails)

        if EMAIL_MODE == "only_email" and not has_email:
            continue

        score = 5 if has_email else 0

        results.append({
            "email": email,
            "link": link,
            "content": raw,
            "score": score
        })

    results.sort(key=lambda x: -x["score"])
    return results[:RESULT_LIMIT]

# ==============================
# TELEGRAM
# ==============================
def send(results):
    if not TOKEN or not CHAT_ID:
        return

    if not results:
        msg = f"📭 No results\n\n🔎 {SEARCH_QUERY}"
    else:
        msg = f"🔥 {SEARCH_QUERY}\n\n"
        for r in results[:5]:
            msg += f"📧 {r['email']}\n🔗 {r['link']}\n\n"

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    posts = fetch_posts()
    results = process_posts(posts)

    send(results)

    # IMPORTANT → JSON output for UI
    print(json.dumps(results))
