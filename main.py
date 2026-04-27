# =====================================
# LinkedIn Hiring Radar
# Version: v1.0.3-stable-final
# Status: STABLE + TELEGRAM + CLEAN STDOUT
# =====================================

import requests, os, re, time, json, sys
from functools import lru_cache
from sentence_transformers import SentenceTransformer, util

@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = get_model()


APIFY_TOKEN = os.getenv("APIFY_TOKEN")

import sys
print("TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"), file=sys.stderr)
print("CHAT_ID:", os.getenv("TELEGRAM_CHAT_ID"), file=sys.stderr)

import sys

args = sys.argv

SEARCH_QUERY = args[1] if len(args) > 1 else ""
POSTED_LIMIT = args[2] if len(args) > 2 else "24h"
EMAIL_MODE = args[3] if len(args) > 3 else "prefer_email"
RESULT_LIMIT = int(args[4]) if len(args) > 4 else 20
LOCATION_KEYWORDS = args[5] if len(args) > 5 else ""

TELEGRAM_BOT_TOKEN = args[6] if len(args) > 6 else ""
TELEGRAM_CHAT_ID = args[7] if len(args) > 7 else ""

ACTOR_ID = "harvestapi~linkedin-post-search"

# ==============================
# TELEGRAM
# ==============================
def send_telegram(results):
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()

    if not token or not chat_id:
        print("TELEGRAM: Missing token or chat_id", file=sys.stderr)
        return

    print(f"TELEGRAM: Sending {min(len(results),5)} messages", file=sys.stderr)

    for r in results[:5]:
        if not r.get("link"):
            continue

        msg = f"""🔥 New Job Lead

📧 {r['email']}
⭐ Score: {r['score']}

{r['content'][:200]}

🔗 {r['link']}"""

        try:
            res = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat_id, "text": msg},
                timeout=10
            )
            print("TELEGRAM STATUS:", res.status_code, file=sys.stderr)
            time.sleep(0.3)
        except Exception as e:
            print("TELEGRAM ERROR:", str(e), file=sys.stderr)
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
# PROCESS (UNCHANGED LOGIC)
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
        "insight", "story", "I'm curious"
    ]

    for p in posts:
        text = p.get("content") or ""
        link = p.get("linkedinUrl")

        if not text or not link or link in seen:
            continue
        seen.add(link)

        clean = re.sub(r"#\w+", "", text.lower())

        if any(bp in clean for bp in bad_patterns):
            continue

        strict_match = any(k in clean for k in strict_intent)
        weak_match = any(k in clean for k in weak_intent)

        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        has_email = bool(emails)
        email = emails[0] if has_email else "Not found"

        if EMAIL_MODE == "only_email" and not has_email:
            continue

        emb = model.encode(text[:400])
        sim = util.cos_sim(query_emb, emb).item()

        if sim < 0.05:
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

        if strict_match:
            results.append(obj)
        elif weak_match or has_email:
            fallback.append(obj)

    # guaranteed fallback
    if results:
        final = results
    elif fallback:
        final = fallback
    else:
        final = [
            {
                "email": "Not found",
                "link": p.get("linkedinUrl"),
                "content": p.get("content", ""),
                "score": 0,
                "semantic_score": 0
            }
            for p in posts if p.get("content") and p.get("linkedinUrl")
        ]

    final.sort(key=lambda x: (x["email"] == "Not found", -x["score"]))

    return final[:RESULT_LIMIT]

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    try:
        posts = fetch_posts()
        print("DEBUG posts:", len(posts), file=sys.stderr)

        results = process(posts)
        print("DEBUG results:", len(results), file=sys.stderr)

        if results:
            send_telegram(results)
        else:
            print("TELEGRAM: No results to send", file=sys.stderr)

        print(json.dumps(results))  # ONLY JSON
    except Exception as e:
        print("ERROR:", str(e), file=sys.stderr)
        print(json.dumps([]))
