import os
import json

from query_builder import build_queries
from scoring import (
    calculate_intent_score,
    calculate_role_score,
    is_irrelevant,
    final_score
)

# ==============================
# ENV INPUTS
# ==============================
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "product owner")
LOCATION = os.getenv("LOCATION_KEYWORDS", "")
RESULT_LIMIT = int(os.getenv("RESULT_LIMIT", 20))

# ==============================
# MOCK / EXISTING FETCH FUNCTION
# Replace this with your real function
# ==============================
def fetch_linkedin_posts(query):
    """
    Expected return format:
    [
        {
            "content": "...",
            "link": "...",
            "email": "...",
            "semantic_score": 0.0
        }
    ]
    """
    # 👉 Replace with your real scraping/API logic
    return []


# ==============================
# QUERY EXPANSION
# ==============================
queries = build_queries(SEARCH_QUERY, LOCATION)

all_results = []

# ==============================
# FETCH + SCORE
# ==============================
for query in queries:
    results = fetch_linkedin_posts(query)

    for r in results:
        content = r.get("content", "")
        semantic_score = r.get("semantic_score", 0)

        intent_score = calculate_intent_score(content)
        role_score = calculate_role_score(content)

        # 🔴 FILTER 1: Must be hiring intent
        if intent_score < 2:
            continue

        # 🔴 FILTER 2: Remove irrelevant roles
        if is_irrelevant(content, role_score):
            continue

        score = final_score(semantic_score, intent_score, role_score)

        r["intent_score"] = intent_score
        r["role_score"] = role_score
        r["score"] = round(score, 2)

        all_results.append(r)


# ==============================
# SORT + DEDUP
# ==============================
# Deduplicate by link
unique = {}
for r in all_results:
    unique[r["link"]] = r

all_results = list(unique.values())

# Sort by score
all_results = sorted(all_results, key=lambda x: x["score"], reverse=True)

# Limit
final_results = all_results[:RESULT_LIMIT]

# ==============================
# OUTPUT
# ==============================
print(json.dumps(final_results))
