# =====================================
# LinkedIn Hiring Radar
# Version: v0.2.9.1
# File: main.py
# =====================================

import requests, os, re, time, json
from functools import lru_cache
from sentence_transformers import SentenceTransformer, util

# ==============================
# MODEL
# ==============================
@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = get_model()

# ==============================
# ENV
# ==============================
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "").strip()
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

POSTED_LIMIT = os.getenv("POSTED_LIMIT", "24h")
RESULT_LIMIT = int(os.getenv("RESULT_LIMIT", "20"))
EMAIL_MODE = os.getenv("EMAIL_MODE", "prefer_email").lower()

ACTOR_ID = "harvestapi~linkedin-post-search"

# ==============================
# QUERY
# ==============================
def generate_queries(role):
    role = role.lower().strip()
    return list(set([
        f"hiring {role}",
        f"{role} job",
        f"{role} opening",
        f"looking for {role}"
    ]))

# ==============================
# FETCH
# ==============================
def fetch_posts():
    if not SEARCH_QUERY or not APIFY_TOKEN:
        return []

    all_posts = []

    for q in generate_queries(SEARCH_QUERY):
        payload = {
            "maxPosts": 10,
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

        dataset_id = None
        for _ in range(20):
            status = requests.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
            ).json()

            if status["data"]["status"] == "SUCCEEDED":
                dataset_id = status["data"]["defaultDatasetId"]
                break
            time.sleep(2)

        if not dataset_id:
            continue

        posts = requests.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&token={APIFY_TOKEN}"
        ).json()

        all_posts.extend(posts)

    return all_posts

# ==============================
# PROCESS
# ==============================
def process(posts):
    results = []
    fallback = []
    seen = set()

    if not SEARCH_QUERY:
        return []

    query_emb = model.encode(SEARCH_QUERY)

    ROLE_MAP = {
        "product owner": ["product owner", "product manager"],
        "business analyst": ["business analyst"],
        "customer success manager": ["customer success manager"]
    }

    roles = ROLE_MAP.get(SEARCH_QUERY.lower(), [SEARCH_QUERY.lower()])

    intent_keywords = [
        "hiring", "we are hiring", "looking for", "job opening",
        "apply", "send your resume", "share your resume",
        "email your resume", "position", "vacancy"
    ]

    # 🔥 NEW: noise filter (SAFE ADDITION)
    bad_patterns = [
        "hot take",
        "lessons",
        "most people think",
        "my thoughts",
        "opinion",
        "insight",
        "story",
    ]

    for p in posts:
        text = p.get("content") or ""
        link = p.get("linkedinUrl")

        if not text or not link or link in seen:
            continue
        seen.add(link)

        clean = re.sub(r"#\w+", "", text.lower())

        # 🔥 NEW: remove non-job content
        if any(bp in clean for bp in bad_patterns):
            continue

        # ==============================
        # INTENT
        # ==============================
        intent_match = any(k in clean for k in intent_keywords)
        fallback_intent = any(x in clean for x in ["hiring", "job", "opening"])

        allow_fallback = not intent_match

        # ==============================
        # ROLE MATCH
        # ==============================
        role_match = any(f" {r} " in f" {clean} " for r in roles)

        # 🔥 NEW: ensure relevance
        if not role_match and not intent_match:
            continue

        # ==============================
        # EMAIL
        # ==============================
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        has_email = bool(emails)
        email = emails[0] if has_email else "Not found"

        if EMAIL_MODE == "only_email" and not has_email:
            continue

        # ==============================
        # SEMANTIC
        # ==============================
        emb = model.encode(text[:400])
        sim = util.cos_sim(query_emb, emb).item()

        if sim < 0.08 and not allow_fallback:
            continue

        score = sim + (0.3 if has_email else 0)

        if "apply" in clean or "send your resume" in clean:
            score += 0.2

        if not intent_match and sim < 0.15:
            continue

        obj = {
            "email": email,
            "link": link,
            "content": text,
            "score": round(score, 2),
            "semantic_score": round(sim, 2)
        }

        if role_match:
            results.append(obj)
        else:
            fallback.append(obj)

    final = results if results else fallback
    final.sort(key=lambda x: (x["email"] == "Not found", -x["score"]))

    return final[:RESULT_LIMIT]

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    try:
        posts = fetch_posts()
        results = process(posts)
        print(json.dumps(results))
    except:
        print(json.dumps([]))
