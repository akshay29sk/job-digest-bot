# =====================================
# LinkedIn Hiring Radar
# Version: v0.2.4
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
# AUTH
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
SEARCH_QUERY = os.getenv("SEARCH_QUERY")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

POSTED_LIMIT = os.getenv("POSTED_LIMIT", "24h")
MAX_POSTS = int(os.getenv("MAX_POSTS", "50"))
RESULT_LIMIT = int(os.getenv("RESULT_LIMIT", "20"))
EMAIL_MODE = os.getenv("EMAIL_MODE", "prefer_email").lower()

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
        f"{role} opening"
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
            "postedLimit": POSTED_LIMIT
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
            time.sleep(2)

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
    text = re.sub(r"#\w+", "", text)
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
        "customer success manager": ["customer success manager"]
    }

    role_variants = ROLE_MAP.get(clean_query, [clean_query])

    for post in posts:
        raw = post.get("content") or ""
        link = post.get("linkedinUrl")

        if not raw or not link or link in seen:
            continue

        seen.add(link)

        if not is_english(raw[:300]):
            continue

        text = clean_text(raw)

        if not any(x in text for x in ["hiring", "job", "role", "opening", "apply"]):
            continue

        role_match = any(role in text for role in role_variants)

        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", raw)
        has_email = bool(emails)
        email = emails[0] if has_email else "Not found"

        if EMAIL_MODE == "only_email" and not has_email:
            continue
        if EMAIL_MODE == "no_email" and has_email:
            continue

        emb = model.encode(raw[:400])
        sim = util.cos_sim(query_embedding, emb).item()

        if sim < 0.15:
            continue

        score = sim + (0.3 if has_email else 0)

        obj = {
            "email": email,
            "link": link,
            "content": raw,
            "score": round(score, 2),
            "semantic_score": round(sim, 2)
        }

        if role_match:
            results.append(obj)
        else:
            fallback.append(obj)

    final = results if results else fallback

    final.sort(key=lambda x: (x["email"] == "Not found", -x["score"]))

    print("RESULT COUNT:", len(final))
    print(json.dumps(final))

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    posts = fetch_posts()
    process_posts(posts)
