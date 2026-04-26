# =====================================
# LinkedIn Hiring Radar
# Version: v1.0.2-stable-telegram
# Status: STABLE + SMART FILTER + TELEGRAM
# =====================================

import requests, os, re, time, json
from functools import lru_cache
from sentence_transformers import SentenceTransformer, util

@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = get_model()

SEARCH_QUERY = os.getenv("SEARCH_QUERY", "").strip()
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

POSTED_LIMIT = os.getenv("POSTED_LIMIT", "24h")
RESULT_LIMIT = int(os.getenv("RESULT_LIMIT", "20"))
EMAIL_MODE = os.getenv("EMAIL_MODE", "prefer_email").lower()

ACTOR_ID = "harvestapi~linkedin-post-search"

# ==============================
# TELEGRAM
# ==============================
def send_telegram(results):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return

    for r in results[:5]:  # limit messages
        msg = f"""🔥 New Job Lead

📧 {r['email']}
⭐ Score: {r['score']}

{r['content'][:200]}

🔗 {r['link']}
"""

        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat_id, "text": msg}
            )
        except:
            pass

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

    strict_intent = [
        "we are hiring", "we're hiring", "hiring",
        "looking for", "job opening", "opening for",
        "apply", "apply now",
        "send your resume", "share your resume",
        "email your resume"
    ]

    weak_intent = ["position", "vacancy", "dm me", "reach out"]

    bad_patterns = [
        "hot take", "lessons", "most people think",
        "discussion", "my thoughts", "opinion",
        "insight", "story"
    ]

    for p in posts:
        text = p.get("content") or ""
        link = p.get("linkedinUrl")

        if not text or not link or link in seen:
            continue
        seen.add(link)

        clean = re.sub(r"#\w+", "", text.lower())

        # ❌ Remove noise
        if any(bp in clean for bp in bad_patterns):
            continue

        strict_match = any(k in clean for k in strict_intent)
        weak_match = any(k in clean for k in weak_intent)

        # Email
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        has_email = bool(emails)
        email = emails[0] if has_email else "Not found"

        if EMAIL_MODE == "only_email" and not has_email:
            continue

        # Semantic
        emb = model.encode(text[:400])
        sim = util.cos_sim(query_emb, emb).item()

        if sim < 0.08:
            continue

        score = sim + (0.3 if has_email else 0)

        if "apply" in clean:
            score += 0.2

        role_match = any(r in clean for r in roles)

        obj = {
            "email": email,
            "link": link,
            "content": text,
            "score": round(score, 2),
            "semantic_score": round(sim, 2)
        }

        # PRIMARY
        if strict_match:
            results.append(obj)

        # FALLBACK
        elif weak_match or has_email:
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

        # 🔥 TELEGRAM TRIGGER
        if results:
            send_telegram(results)

        print(json.dumps(results))
    except:
        print(json.dumps([]))
