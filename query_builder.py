def build_queries(role, location=""):
    role = role.lower().strip()

    base_queries = [
        f"hiring {role}",
        f"{role} hiring",
        f"opening for {role}",
        f"{role} vacancy",
        f"looking for {role}",
        f"{role} position",
        f"urgent hiring {role}"
    ]

    if location and location != "global":
        location_queries = []
        for q in base_queries:
            location_queries.append(f"{q} {location}")
        return base_queries + location_queries

    return base_queries
