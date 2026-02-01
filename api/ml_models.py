"""
Machine Learning Model Classes

This module contains the class definitions for all ML models used in the system.
These classes must be defined here for pickle to properly deserialize the models.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any


from sklearn.decomposition import TruncatedSVD

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


def get_cf_score(model, user_id: int, movie_id: int) -> float:
    """
    Get collaborative filtering prediction score

    Args:
        model: Trained collaborative filtering model
        user_id: User ID
        movie_id: Movie ID

    Returns:
        Predicted rating
    """
    prediction = model.predict(user_id, movie_id)
    return prediction.est


def get_content_score(
    movie_id: int,
    user_top_movies: List[int],
    cosine_sim: np.ndarray,
    movies: pd.DataFrame
) -> float:
    """
    Get content-based similarity score

    Args:
        movie_id: Target movie ID
        user_top_movies: List of user's top-rated movie IDs
        cosine_sim: Content similarity matrix
        movies: Movies dataframe

    Returns:
        Average similarity score
    """
    try:
        # Get index of the movie
        movie_idx = movies[movies['movieId'] == movie_id].index[0]

        # Calculate average similarity to user's top movies
        similarities = []
        for top_movie_id in user_top_movies:
            top_idx = movies[movies['movieId'] == top_movie_id].index[0]
            similarities.append(cosine_sim[movie_idx][top_idx])

        return np.mean(similarities) if similarities else 0
    except:
        return 0


class HybridRecommender:
    """
    Hybrid Recommender combining Collaborative Filtering and Content-Based filtering

    This class implements a weighted hybrid approach that combines:
    - Collaborative Filtering (CF): Predictions based on user-item interactions
    - Content-Based (CB): Similarity based on movie features (genres)

    The hybrid score is calculated as: (cf_weight * cf_score) + (cb_weight * cb_score)
    """

    def __init__(
        self,
        cf_model,
        content_sim_matrix: np.ndarray,
        movies_df: pd.DataFrame,
        cf_weight: float = 0.6,
        cb_weight: float = 0.4
    ):
        """
        Initialize hybrid recommender

        Parameters:
            cf_model: Trained collaborative filtering model (e.g., SVD)
            content_sim_matrix: Content similarity matrix (cosine similarity of movie features)
            movies_df: Movies dataframe with columns: movieId, title, genres
            cf_weight: Weight for collaborative filtering component (default 0.6)
            cb_weight: Weight for content-based component (default 0.4)

        Raises:
            ValueError: If weights don't sum to 1.0
        """
        self.cf_model = cf_model
        self.content_sim = content_sim_matrix
        self.movies = movies_df
        self.cf_weight = cf_weight
        self.cb_weight = cb_weight

        # Validate weights
        if abs(cf_weight + cb_weight - 1.0) > 0.001:
            raise ValueError("Weights must sum to 1.0")

    def get_recommendations(
        self,
        user_id: int,
        ratings_df: pd.DataFrame,
        n: int = 10,
        min_cf_score: float = 2.5
    ) -> List[Dict[str, Any]]:
        """
        Get hybrid recommendations for a user

        This method:
        1. Identifies user's top-rated movies (rating >= 4.0)
        2. Finds movies the user hasn't rated
        3. Calculates hybrid scores combining CF and CB approaches
        4. Returns top N movies ranked by hybrid score

        Parameters:
            user_id: User ID to generate recommendations for
            ratings_df: Ratings dataframe with columns: userId, movieId, rating
            n: Number of recommendations to return (default 10)
            min_cf_score: Minimum CF score threshold for filtering (default 2.5)

        Returns:
            List of dictionaries containing:
                - movieId: Movie ID
                - title: Movie title
                - genres: Movie genres
                - predicted_rating: Final hybrid score (for API compatibility)
                (Optional internal fields: cf_score, cb_score, hybrid_score)
        """
        # Get user's top-rated movies for content-based component
        user_ratings = ratings_df[ratings_df['userId'] == user_id]
        top_rated = user_ratings[user_ratings['rating'] >= 4.0].nlargest(5, 'rating')
        user_top_movies = top_rated['movieId'].values

        # Get movies user hasn't rated
        all_movie_ids = self.movies['movieId'].unique()
        rated_movies = user_ratings['movieId'].values
        unrated_movies = [mid for mid in all_movie_ids if mid not in rated_movies]

        # Calculate hybrid scores
        hybrid_scores = []

        for movie_id in unrated_movies:
            # Collaborative filtering score (normalize to 0-1 range)
            cf_score = get_cf_score(self.cf_model, user_id, movie_id)
            cf_normalized = (cf_score - 0.5) / (5.0 - 0.5)  # Scale from [0.5, 5] to [0, 1]

            # Content-based score (already in 0-1 range from cosine similarity)
            cb_score = get_content_score(
                movie_id,
                user_top_movies,
                self.content_sim,
                self.movies
            )

            # Hybrid score (weighted combination)
            hybrid_score = (self.cf_weight * cf_normalized +
                          self.cb_weight * cb_score)

            # Only include if CF score meets minimum threshold
            if cf_score >= min_cf_score:
                hybrid_scores.append({
                    'movieId': movie_id,
                    'cf_score': cf_score,
                    'cb_score': cb_score,
                    'hybrid_score': hybrid_score
                })

        # Sort by hybrid score (descending)
        hybrid_scores.sort(key=lambda x: x['hybrid_score'], reverse=True)

        # Get top N with movie details
        recommendations = []
        for item in hybrid_scores[:n]:
            movie_info = self.movies[self.movies['movieId'] == item['movieId']].iloc[0]
            recommendations.append({
                'movieId': int(item['movieId']),
                'title': movie_info['title'],
                'genres': movie_info['genres'],
                'predicted_rating': float(item['cf_score'])  # Use CF score as predicted rating
            })

        return recommendations

    def __repr__(self) -> str:
        """String representation of the hybrid recommender"""
        return (f"HybridRecommender(cf_weight={self.cf_weight}, "
                f"cb_weight={self.cb_weight}, "
                f"movies={len(self.movies)})")
