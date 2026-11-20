"""Feature preparation for content-based action matching."""
def action_features(actions):
    """Return category and action text fields for vectorization."""
    return [f"{a.get('category', '')} {a.get('title', '')} {a.get('description', '')}" for a in actions]
