# =====================================
# LinkedIn Hiring Radar
# Version: v0.2.3
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

# ==============================
# HF LOGIN
# ==============================
hf_token = os.getenv("HF_TOKEN")
if hf_token:
    login(token=hf_token.strip())

# ==============================
# MODEL
# ==============================
@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = get_model()

# ==============================
# ENV
# ==============================
def get_env(name, default=None):
    return os.getenv(name) or default

SEARCH_QUERY = get_env("SEARCH_QUERY")
APIFY_TOKEN = get_env("APIFY_TOKEN")

POSTED_LIMIT = get_env("POSTED_LIMIT", "24h")
MAX_POSTS = int(get_env("MAX_POSTS", "50"))
RESULT_LIMIT = int(get_env("RESULT_LIMIT", "20"))
EMAIL_MODE = get_env("EMAIL_MODE", "prefer_email").lower()

ACTOR_ID = "harvestapi~linkedin-post-search"

# ==============================
# QUERY GENERATION
# ==============================
def generate_queries(role):
    role = role.lower().strip()
    return list(set([
        f"hiring {role}",
        f"looking for {role}",
        f"{role} job",
        f"{role} role",
        f"{role} opening",
        f"{role} hiring"
    ]))

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
# HELPERS
# ==============================
def is_english(text):
    try:
        text.encode("ascii")
        return True
    except:
        return False

def clean_text(text):
    text = re.sub(r"#\w+", "", text)  # remove hashtags
    return text.lower()

# ==============================
# PROCESS
# ==============================
def process_posts(posts):
    results = []
    fallback = []
    seen = set()

    query_embedding = model.encode(SEARCH_QUERY)

    clean_query = SEARCH_QUERY.lower().strip()

    ROLE_MAP = {
        "product owner": ["product owner", "product manager"],
        "business analyst": ["business analyst"],
        "customer success manager": ["customer success manager"],
    }

    role_variants = ROLE_MAP.get(clean_query, [clean_query])

    for post in posts:
        raw_text = post.get("content") or ""
        link = post.get("linkedinUrl")

        if not raw_text or not link or link in seen:
            continue

        seen.add(link)

        if not is_english(raw_text[:300]):
            continue

        text = clean_text(raw_text)

        if not any(x in text for x in ["hiring", "job", "role", "opening", "apply"]):
            continue

        role_match = any(role in text for role in role_variants)

        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", raw_text)
        emails = [e.split("hashtag")[0] for e in emails]

        has_email = bool(emails)
        email = emails[0] if has_email else "Not found"

        if EMAIL_MODE == "only_email" and not has_email:
            continue
        if EMAIL_MODE == "no_email" and has_email:
            continue

        post_embedding = model.encode(raw_text[:500])
        semantic_score = util.cos_sim(query_embedding, post_embedding).item()

        if semantic_score < 0.15:
            continue

        score = semantic_score + (0.3 if has_email else 0)

        result = {
            "email": email,
            "link": link,
            "content": raw_text,
            "score": round(score, 2),
            "semantic_score": round(semantic_score, 2)
        }

        if role_match:
            results.append(result)
        else:
            fallback.append(result)

    final = results if results else fallback

    print("RESULT COUNT:", len(final))

    final.sort(key=lambda x: (x["email"] == "Not found", -x["score"]))

    return final[:RESULT_LIMIT]

# ==============================
# TELEGRAM
# ==============================
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

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    posts = fetch_posts()
    results = process_posts(posts)

    send(results)
    print(json.dumps(results))
