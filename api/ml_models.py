"""
Machine Learning Model Classes

This module contains the class definitions for all ML models used in the system.
These classes must be defined here for pickle to properly deserialize the models.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any


from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ScikitLearnSVD:
    """
    SVD implementation using scikit-learn's TruncatedSVD.
    This replaces the scikit-surprise implementation to avoid build tool requirements.
    """
    def __init__(self, n_components=20, random_state=42):
        self.model = TruncatedSVD(n_components=n_components, random_state=random_state)
        self.user_map = {}
        self.movie_map = {}
        self.reverse_user_map = {}
        self.reverse_movie_map = {}
        self.user_factors = None
        self.item_factors = None
        self.global_mean = 3.5
        
    def fit(self, ratings_df):
        """
        Fit the SVD model to the ratings dataframe
        """
        self.global_mean = ratings_df['rating'].mean()
        
        # Create mapping for users and movies
        unique_users = ratings_df['userId'].unique()
        unique_movies = ratings_df['movieId'].unique()
        
        self.user_map = {uid: i for i, uid in enumerate(unique_users)}
        self.movie_map = {mid: i for i, mid in enumerate(unique_movies)}
        self.reverse_user_map = {i: uid for uid, i in self.user_map.items()}
        self.reverse_movie_map = {i: mid for mid, i in self.movie_map.items()}
        
        # Create sparse user-item matrix
        # Pivot is memory intensive, but for MovieLens small it's fine
        # Fill with 0 (assuming missing = 0 for SVD input usually implies unrated)
        # Note: Standard SVD for recommender usually treats missing as missing, 
        # but TruncatedSVD expects a full matrix. We subtract mean to center it.
        
        user_ids = ratings_df['userId'].map(self.user_map)
        movie_ids = ratings_df['movieId'].map(self.movie_map)
        
        # Construct pivot table manually (safer for large data than pivot_table)
        from scipy.sparse import csr_matrix
        import numpy as np
        
        rows = user_ids.values
        cols = movie_ids.values
        data = (ratings_df['rating'] - self.global_mean).values
        
        sparse_matrix = csr_matrix((data, (rows, cols)), 
                                   shape=(len(unique_users), len(unique_movies)))
        
        # Fit model
        self.user_factors = self.model.fit_transform(sparse_matrix)
        self.item_factors = self.model.components_
        
        return self

    def predict(self, user_id, movie_id):
        """
        Predict rating for user_id and movie_id
        Returns an object with .est attribute to match Surprise interface
        """
        class Prediction:
            def __init__(self, est):
                self.est = est
                
        # If user or movie not known, return global mean
        if user_id not in self.user_map or movie_id not in self.movie_map:
            return Prediction(self.global_mean)
            
        u_idx = self.user_map[user_id]
        m_idx = self.movie_map[movie_id]
        
        # Dot product + global mean
        # user_factors [u_idx] shape (n_components,)
        # item_factors [:, m_idx] shape (n_components,)
        
        # item_factors is (n_components, n_features), so we access column m_idx 
        # Wait, components_ is (n_components, n_features). 
        # So item vector is components_[:, m_idx]
        
        pred = float(np.dot(self.user_factors[u_idx], self.item_factors[:, m_idx]))
        pred += self.global_mean
        
        # Clip to valid range
        pred = max(0.5, min(5.0, pred))
        
        return Prediction(pred)


class ScikitLearnKNN:
    """Mock KNN implementation for fallback."""
    def __init__(self, user_based=True):
        self.user_based = user_based
        self.global_mean = 3.5
        
    def fit(self, ratings_df):
        self.global_mean = ratings_df['rating'].mean()
        return self
        
    def predict(self, user_id, movie_id):
        class Prediction:
            def __init__(self, est):
                self.est = est
        return Prediction(self.global_mean)


def build_genre_matrix(movies_df: pd.DataFrame):
    """
    Build a sparse genre matrix to save memory.
    """
    from sklearn.feature_extraction.text import CountVectorizer
    genre_series = movies_df["genres"].fillna("")
    vectorizer = CountVectorizer(token_pattern=r"[^|]+")
    return vectorizer.fit_transform(genre_series)


def get_cf_score(model, user_id: int, movie_id: int) -> float:
    """
    Get collaborative filtering prediction score
    """
    prediction = model.predict(user_id, movie_id)
    return prediction.est


def get_content_score_optimized(
    movie_idx: int,
    user_top_indices: List[int],
    genre_matrix
) -> float:
    """
    Calculate content score on-the-fly using sparse matrix multiplication.
    This uses almost NO memory compared to the 750MB matrix.
    """
    if not user_top_indices:
        return 0.0
    
    from sklearn.metrics.pairwise import cosine_similarity
    
    # Calculate similarity between the target movie and the user's top movies
    target_vec = genre_matrix[movie_idx]
    top_vecs = genre_matrix[user_top_indices]
    
    sims = cosine_similarity(target_vec, top_vecs).flatten()
    return np.mean(sims)


class HybridRecommender:
    """
    Hybrid Recommender optimized for low-memory (Render Free Tier).
    """

    def __init__(
        self,
        cf_model,
        genre_matrix,
        movies_df: pd.DataFrame,
        cf_weight: float = 0.6,
        cb_weight: float = 0.4
    ):
        self.cf_model = cf_model
        self.genre_matrix = genre_matrix
        self.movies = movies_df
        self.cf_weight = cf_weight
        self.cb_weight = cb_weight
        
        # Create a mapping from movie ID to dataframe index for fast lookup
        self.id_to_idx = {id: i for i, id in enumerate(self.movies['movieId'])}

    def get_recommendations(
        self,
        user_id: int,
        ratings_df: pd.DataFrame,
        n: int = 10,
        min_cf_score: float = 2.5
    ) -> List[Dict[str, Any]]:
        # Get user's top-rated movies
        user_ratings = ratings_df[ratings_df['userId'] == user_id]
        top_rated = user_ratings[user_ratings['rating'] >= 4.0].nlargest(5, 'rating')
        user_top_ids = top_rated['movieId'].values
        user_top_indices = [self.id_to_idx[mid] for mid in user_top_ids if mid in self.id_to_idx]

        # Get movies user hasn't rated
        all_movie_ids = self.movies['movieId'].values
        rated_movies = set(user_ratings['movieId'].values)
        unrated_movies = [mid for mid in all_movie_ids if mid not in rated_movies]

        # Calculate hybrid scores
        hybrid_scores = []

        for movie_id in unrated_movies:
            cf_score = get_cf_score(self.cf_model, user_id, movie_id)
            if cf_score < min_cf_score:
                continue
                
            cf_normalized = (cf_score - 0.5) / (5.0 - 0.5)

            # Get content score on the fly
            m_idx = self.id_to_idx.get(movie_id)
            cb_score = 0.0
            if m_idx is not None:
                cb_score = get_content_score_optimized(m_idx, user_top_indices, self.genre_matrix)

            hybrid_score = (self.cf_weight * cf_normalized + self.cb_weight * cb_score)

            hybrid_scores.append({
                'movieId': movie_id,
                'cf_score': cf_score,
                'hybrid_score': hybrid_score
            })

        # Sort and return
        hybrid_scores.sort(key=lambda x: x['hybrid_score'], reverse=True)

        recommendations = []
        for item in hybrid_scores[:n]:
            movie_info = self.movies[self.movies['movieId'] == item['movieId']].iloc[0]
            recommendations.append({
                'movieId': int(item['movieId']),
                'title': movie_info['title'],
                'genres': movie_info['genres'],
                'predicted_rating': float(item['cf_score'])
            })

        return recommendations

    def __repr__(self) -> str:
        """String representation of the hybrid recommender"""
        return (f"HybridRecommender(cf_weight={self.cf_weight}, "
                f"cb_weight={self.cb_weight}, "
                f"movies={len(self.movies)})")
