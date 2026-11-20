"""Optional TF-IDF and cosine-similarity helpers for content-based matching."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def similarity_scores(query, documents):
    matrix = TfidfVectorizer().fit_transform([query, *documents])
    return cosine_similarity(matrix[0:1], matrix[1:]).ravel()
