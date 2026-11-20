"""Rule-based annual footprint estimate; replace sample factors with sourced data."""
def estimate_category(activity, emission_factor):
    if activity < 0 or emission_factor < 0:
        raise ValueError("Activity and emission factor must be non-negative")
    return activity * emission_factor

def estimate_footprint(profile, factors):
    """Return category totals in kg CO2e. Factors must match activity units."""
    return {category: estimate_category(value, factors[category]) for category, value in profile.items()}
