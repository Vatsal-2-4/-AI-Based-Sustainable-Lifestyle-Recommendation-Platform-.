"""Application-facing interface for personalized content recommendations."""
from ml.models.content_recommender import recommend

def recommend_for_profile(profile, top_n=6):
    """Recommend catalogue actions matching a validated lifestyle profile."""
    return recommend(profile, top_n=top_n)
