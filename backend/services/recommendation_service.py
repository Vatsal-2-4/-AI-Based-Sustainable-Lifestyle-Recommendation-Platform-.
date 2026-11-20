"""Eligibility filtering and transparent weighted action ranking."""
def rank_actions(actions, profile, weights=None):
    weights = weights or {"impact": 0.5, "affordability": 0.2, "ease": 0.15, "preference": 0.15}
    eligible = [row for row in actions if row.get("eligible", True)]
    for row in eligible:
        row["score"] = (weights["impact"] * row.get("impact_score", 0) +
                        weights["affordability"] * row.get("affordability_score", 0) +
                        weights["ease"] * row.get("ease_score", 0) +
                        weights["preference"] * row.get("preference_score", 0))
    return sorted(eligible, key=lambda row: row["score"], reverse=True)
