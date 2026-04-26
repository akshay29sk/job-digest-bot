import os
import json

from query_builder import build_queries
from scoring import (
    calculate_intent_score,
    calculate_role_score,
    final_score
)

# ==============================
# ENV INPUTS
# ==============================
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "product owner")
LOCATION = os.getenv("LOCATION_KEYWORDS", "")
RESULT_LIMIT = int(os.getenv("RESULT_LIMIT", 20))
EXTRA_ROLES = os.getenv("ROLE_KEYWORDS", "")

# ==============================
# FETCH FUNCTION (YOUR EXISTING)
# ==============================
def fetch_linkedin_posts(query):
    # ⚠️ Replace with your actual logic
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
        role_score = calculate_role_score(content, EXTRA_ROLES)

        # ✅ Relaxed intent filter
        if intent_score < 1:
            continue

        # ✅ Soft role filtering (NOT aggressive)
        if role_score == 0:
            # allow only if strong hiring signal
            if intent_score < 2:
                continue

        score = final_score(semantic_score, intent_score, role_score)

        r["intent_score"] = intent_score
        r["role_score"] = role_score
        r["score"] = round(score, 2)

        all_results.append(r)

# ==============================
# DEDUP
# ==============================
unique = {}
for r in all_results:
    unique[r.get("link")] = r

all_results = list(unique.values())

# ==============================
# SORT + LIMIT
# ==============================
all_results = sorted(all_results, key=lambda x: x["score"], reverse=True)
final_results = all_results[:RESULT_LIMIT]

# ==============================
# OUTPUT
# ==============================
print(json.dumps(final_results))
