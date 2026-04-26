import requests
import os
import re
import time

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

SEARCH_QUERY = os.getenv("SEARCH_QUERY")
ROLE_KEYWORDS = os.getenv("ROLE_KEYWORDS")
HIRING_KEYWORDS = os.getenv("HIRING_KEYWORDS")
MAX_POSTS = int(os.getenv("MAX_POSTS"))
POSTED_LIMIT = os.getenv("POSTED_LIMIT")

if not SEARCH_QUERY:
    raise Exception("SEARCH_QUERY missing")
if not ROLE_KEYWORDS:
    raise Exception("ROLE_KEYWORDS missing")
if not HIRING_KEYWORDS:
    raise Exception("HIRING_KEYWORDS missing")

ACTOR_ID = "harvestapi~linkedin-post-search"


def fetch_posts():
    queries = [q.strip() for q in SEARCH_QUERY.split(",") if q.strip()]
    print("🔎 Queries:", queries)

    run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"

    payload = {
        "searchQueries": queries,
        "maxPosts": MAX_POSTS,
        "postedLimit": POSTED_LIMIT,
        "sortBy": "date",
        "scrapeComments": False,
        "scrapeReactions": False
    }

    run = requests.post(run_url, json=payload).json()

    if "data" not in run:
        print("Run error:", run)
        return []

    run_id = run["data"]["id"]
    dataset_id = run["data"]["defaultDatasetId"]

    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"

    for _ in range(24):
        status = requests.get(status_url).json()
        state = status["data"]["status"]
        print("Status:", state)

        if state == "SUCCEEDED":
            break
        if state in ["FAILED", "ABORTED"]:
            return []

        time.sleep(5)

    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&token={APIFY_TOKEN}"
    posts = requests.get(dataset_url).json()

    print("Fetched:", len(posts))
    return posts


def filter_posts(posts):
    results = []
    seen = set()

    role_words = [x.strip().lower() for x in ROLE_KEYWORDS.split(",")]
    hiring_words = [x.strip().lower() for x in HIRING_KEYWORDS.split(",")]

    for post in posts:
        text = (post.get("content") or "").lower()
        link = post.get("linkedinUrl")

        if not text or not link:
            continue

        if not any(x in text for x in role_words):
            continue

        if not any(x in text for x in hiring_words):
            continue

        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        email = emails[0] if emails else "Not found"

        if link in seen:
            continue

        seen.add(link)

        results.append({
            "email": email,
            "link": link
        })

    return results[:5]


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def build_message(results):
    if not results:
        return f"No results today\nQuery: {SEARCH_QUERY}"

    msg = f"LinkedIn Hiring Posts\nQuery: {SEARCH_QUERY}\n\n"

    for i, r in enumerate(results, 1):
        msg += f"{i}\n{r['email']}\n{r['link']}\n\n"

    return msg


if __name__ == "__main__":
    posts = fetch_posts()
    filtered = filter_posts(posts)
    msg = build_message(filtered)

    print(msg)
    send(msg)
