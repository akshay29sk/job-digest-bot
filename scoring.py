def calculate_intent_score(content):
    hiring_keywords = [
        "hiring", "opening", "vacancy", "we are hiring",
        "looking for", "join us", "apply", "send resume", "dm me"
    ]

    content = content.lower()
    return sum(1 for k in hiring_keywords if k in content)


def calculate_role_score(content):
    role_keywords = [
        "product owner",
        "product manager",
        "business analyst",
        "product management"
    ]

    content = content.lower()
    return sum(2 for k in role_keywords if k in content)


def is_irrelevant(content, role_score):
    irrelevant_roles = [
        "hardware engineer",
        "embedded",
        "sales",
        "marketing",
        "technician",
        "video host",
        "machine learning",
        "cybersecurity"
    ]

    content = content.lower()

    if any(r in content for r in irrelevant_roles) and role_score == 0:
        return True

    return False


def final_score(semantic_score, intent_score, role_score):
    return (
        semantic_score * 0.4 +
        intent_score * 10 +
        role_score * 15
    )
