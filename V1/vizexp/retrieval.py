from .charts import categories


def retrieve(library, chart):
    chosen = []
    rejected = []
    chart_categories = categories(chart)
    for rule in library["experiences"]:
        scope = rule["scope"]
        reasons = []
        if rule["status"] != "active":
            reasons.append("inactive_status")
        if rule["provenance"]["evaluation_dependent"]:
            reasons.append("evaluation_dependent")
        if scope["organization"] != "any" and scope["organization"] != chart["organization"]:
            reasons.append("organization_mismatch")
        if "any" not in scope["families"] and chart["family"] not in scope["families"]:
            reasons.append("family_mismatch")
        if "any" not in scope["media"] and chart["media"] not in scope["media"]:
            reasons.append("media_mismatch")
        if "general" not in scope["categories"] and not chart_categories.intersection(scope["categories"]):
            reasons.append("category_mismatch")
        if reasons:
            rejected.append({"id": rule["id"], "reasons": reasons})
        else:
            chosen.append(rule)
    # All in-scope rules are supplied; no arbitrary top-k silently drops a team exception.
    chosen.sort(key=lambda r: (-r["retrieval"]["priority"], r["id"]))
    return chosen, {"categories": sorted(chart_categories), "selected_ids": [r["id"] for r in chosen], "excluded": rejected}
