def calculate_intent_score(content):
    keywords = [
        "hiring", "opening", "vacancy",
        "we are hiring", "looking for",
        "join us", "apply", "send resume", "dm me"
    ]
    content = content.lower()
    return sum(1 for k in keywords if k in content)


def calculate_role_score(content, extra_roles=""):
    base_roles = [
        "product owner",
        "product manager",
        "business analyst",
        "product management"
    ]

    if extra_roles:
        extra = [r.strip().lower() for r in extra_roles.split(",")]
        base_roles.extend(extra)

    content = content.lower()

    score = 0
    for role in base_roles:
        if role in content:
            score += 2

    return score


def final_score(semantic_score, intent_score, role_score):
    return (
        semantic_score * 0.4 +
        intent_score * 10 +
        role_score * 15
    )
