"""Optional grounded LLM explanations. Numeric impact remains catalogue-owned."""
def explain_recommendation(action, profile_summary):
    """Integrate a provider here; default is safe deterministic copy."""
    return f"{action['title']} may suit your profile. Estimated impact: {action['annual_saving_kg']} kg CO2e per year."
