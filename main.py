# =====================================
# LinkedIn Hiring Radar
# Version: v0.1.4.1
# File: main.py
# =====================================

import requests
import os
import re
import time
import json
from functools import lru_cache
from sentence_transformers import SentenceTransformer, util
from huggingface_hub import login

# HF login
hf_token = os.getenv("HF_TOKEN")
if hf_token:
    hf_token = hf_token.strip()
    login(token=hf_token)

@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = get_model()

def get_env(name, default=None):
    val = os.getenv(name)
    return val if val else default

SEARCH_QUERY = get_env("SEARCH_QUERY")
APIFY_TOKEN = get_env("APIFY_TOKEN")

POSTED_LIMIT = get_env("POSTED_LIMIT", "24h")
MAX_POSTS = int(get_env("MAX_POSTS", "50"))
RESULT_LIMIT = int(get_env("RESULT_LIMIT", "20"))
EMAIL_MODE = get_env("EMAIL_MODE", "prefer_email").lower()
LOCATION_KEYWORDS = get_env("LOCATION_KEYWORDS", "global")

ACTOR_ID = "harvestapi~linkedin-post-search"

def generate_queries(base):
    base = base.lower()
    return list(set([
        base,
        base.replace("hiring", "looking for"),
        base.replace("hiring", "job opening")
    ]))

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

def process_posts(posts):
    results = []
    seen = set()

    query_embedding = model.encode(SEARCH_QUERY)

    for post in posts:
        text = (post.get("content") or "")
        lower_text = text.lower()
        link = post.get("linkedinUrl")

        if not text or not link or link in seen:
            continue

        seen.add(link)

        if not any(x in lower_text for x in ["hiring", "looking", "apply", "send cv"]):
            continue

        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", lower_text)
        has_email = bool(emails)
        email = emails[0] if has_email else "Not found"

        if EMAIL_MODE == "only_email" and not has_email:
            continue

        # Semantic scoring
        post_embedding = model.encode(text[:500])
        semantic_score = util.cos_sim(query_embedding, post_embedding).item()

        # 🔥 RELAXED THRESHOLD
        if semantic_score < 0.2:
            continue

        results.append({
            "email": email,
            "link": link,
            "content": text,
            "score": round(semantic_score * 5, 2),
            "semantic_score": round(semantic_score, 2)
        })

    print("RESULT COUNT:", len(results))  # DEBUG

    results.sort(key=lambda x: -x["score"])
    return results[:RESULT_LIMIT]

def send(results):
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    if not TOKEN or not CHAT_ID:
        return

    msg = f"🔥 {SEARCH_QUERY}\n\n"
    for r in results[:5]:
        msg += f"📧 {r['email']}\n🔗 {r['link']}\n\n"

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

if __name__ == "__main__":
    posts = fetch_posts()
    results = process_posts(posts)

    send(results)
    print(json.dumps(results))
