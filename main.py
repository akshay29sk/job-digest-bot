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

APIFY_TOKEN = get_env("APIFY_TOKEN")
ROLE_KEYWORDS = get_env("ROLE_KEYWORDS", "")
POSTED_LIMIT = get_env("POSTED_LIMIT", "24h")
MAX_POSTS = int(get_env("MAX_POSTS", "50"))
RESULT_LIMIT = int(get_env("RESULT_LIMIT", "20"))
EMAIL_MODE = get_env("EMAIL_MODE", "prefer_email").lower()
LOCATION_KEYWORDS = get_env("LOCATION_KEYWORDS", "global")

ACTOR_ID = "harvestapi~linkedin-post-search"

# ==============================
# 🔥 ROLE EXPANSION MAP
# ==============================
ROLE_MAP = {
    "customer success": ["customer success manager", "csm"],
    "business analyst": ["ba", "business analysis"],
    "product manager": ["pm", "product owner"],
    "software engineer": ["developer", "sde", "engineer"]
}

# ==============================
# 🔥 GENERATE SMART QUERIES
# ==============================
def generate_queries(base):
    base = base.lower().strip()
    queries = set()

    # base
    queries.add(base)

    # intent variations
    queries.add(base.replace("hiring", "looking for"))
    queries.add(base.replace("hiring", "job opening"))

    # role expansion
    for key, variations in ROLE_MAP.items():
        if key in base:
            for v in variations:
                queries.add(base.replace(key, v))

    return list(queries)

# ==============================
# FETCH
# ==============================
def fetch_posts():
    all_posts = []
    queries = generate_queries(SEARCH_QUERY)

    print("🔎 Queries:", queries)

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

    print("📦 Total fetched:", len(all_posts))
    return all_posts

# ==============================
# PROCESS + SCORE
# ==============================
def process_posts(posts):
    results = []
    seen = set()

    role_words = [x.strip().lower() for x in ROLE_KEYWORDS.split(",") if x.strip()]
    location_words = [x.strip().lower() for x in LOCATION_KEYWORDS.split(",") if x.strip()]

    for post in posts:
        text = (post.get("content") or "").lower()
        raw = (post.get("content") or "").strip()
        link = post.get("linkedinUrl")

        if not text or not link:
            continue

        if link in seen:
            continue

        seen.add(link)

        # only hiring posts
        if not any(x in text for x in ["hiring", "looking", "apply", "send cv", "resume"]):
            continue

        # role filter
        if role_words and not any(x in text for x in role_words):
            continue

        # location filter
        if LOCATION_KEYWORDS != "global" and location_words:
            if not any(x in text for x in location_words):
                continue

        # email
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        has_email = len(emails) > 0
        email = emails[0] if has_email else "Not found"

        if EMAIL_MODE == "only_email" and not has_email:
            continue
        if EMAIL_MODE == "no_email" and has_email:
            continue

        # scoring
        score = 0

        if has_email:
            score += 5

        if any(x in text for x in ["urgent", "immediate"]):
            score += 3

        if any(x in text for x in ["apply", "send cv"]):
            score += 3

        results.append({
            "email": email,
            "link": link,
            "content": raw,
            "score": score
        })

    results.sort(key=lambda x: -x["score"])

    return results[:RESULT_LIMIT]

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    posts = fetch_posts()
    results = process_posts(posts)

    print(json.dumps(results))
