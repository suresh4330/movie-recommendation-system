"""
Recommendation engine logic for the Movie Recommendation API

This module contains the core recommendation algorithms that use
the trained ML models to generate personalized movie recommendations.
"""

import pandas as pd
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer


def get_recommendations_with_algorithm(
    user_id: int,
    algorithm: str,
    n: int,
    ratings_df: pd.DataFrame,
    movies_df: pd.DataFrame,
    models: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate movie recommendations using the specified algorithm

    Args:
        user_id: User ID to generate recommendations for
        algorithm: Algorithm to use ('svd', 'hybrid', 'user-knn', 'item-knn')
        n: Number of recommendations to generate
        ratings_df: DataFrame containing all user ratings
        movies_df: DataFrame containing movie information
        models: Dictionary containing all loaded ML models

    Returns:
        List of dictionaries containing movie recommendations with predicted ratings

    Raises:
        ValueError: If algorithm is not recognized
        KeyError: If user has no ratings (for collaborative filtering)
    """
    # Select model based on algorithm
    if algorithm == 'svd':
        model = models['svd']
    elif algorithm == 'hybrid':
        # Use hybrid recommender's get_recommendations method
        return models['hybrid'].get_recommendations(user_id, ratings_df, n)
    elif algorithm == 'user-knn':
        model = models['knn_user']
    elif algorithm == 'item-knn':
        model = models['knn_item']
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    # Get user's rated movies
    user_ratings = ratings_df[ratings_df['userId'] == user_id]
    rated_movies = user_ratings['movieId'].values

    # Get all unrated movies
    all_movies = movies_df['movieId'].unique()
    unrated_movies = [m for m in all_movies if m not in rated_movies]

    # Predict ratings for unrated movies
    predictions = []
    for movie_id in unrated_movies:
        pred = model.predict(user_id, movie_id)
        predictions.append((movie_id, pred.est))

    # Sort by predicted rating (descending)
    predictions.sort(key=lambda x: x[1], reverse=True)

    # Get top N with movie details
    recommendations = []
    for movie_id, pred_rating in predictions[:n]:
        movie = movies_df[movies_df['movieId'] == movie_id].iloc[0]
        recommendations.append({
            'movieId': int(movie_id),
            'title': movie['title'],
            'genres': movie['genres'],
            'predicted_rating': float(pred_rating)
        })

    return recommendations


def get_similar_movies(
    movie_id: int,
    n: int,
    movies_df: pd.DataFrame
) -> List[Dict[str, Any]]:
    """
    Find similar movies using content-based filtering (genre similarity)

    Args:
        movie_id: ID of the movie to find similar movies for
        n: Number of similar movies to return
        movies_df: DataFrame containing movie information

    Returns:
        List of dictionaries containing similar movies

    Raises:
        ValueError: If movie_id is not found in the dataset
    """
    # Check if movie exists
    if movie_id not in movies_df['movieId'].values:
        raise ValueError(f"Movie ID {movie_id} not found")

    # Get the target movie
    target_movie = movies_df[movies_df['movieId'] == movie_id].iloc[0]

    # Create genre-based feature vectors
    count_vectorizer = CountVectorizer(token_pattern=r'[^|]+')
    genre_matrix = count_vectorizer.fit_transform(movies_df['genres'])

    # Calculate cosine similarity
    target_idx = movies_df[movies_df['movieId'] == movie_id].index[0]
    similarity_scores = cosine_similarity(genre_matrix[target_idx], genre_matrix).flatten()

    # Get indices of most similar movies (excluding the target movie itself)
    similar_indices = similarity_scores.argsort()[::-1][1:n+1]

    # Build response
    similar_movies = []
    for idx in similar_indices:
        movie = movies_df.iloc[idx]
        similar_movies.append({
            'movieId': int(movie['movieId']),
            'title': movie['title'],
            'genres': movie['genres'],
            'similarity_score': float(similarity_scores[idx])
        })

    return similar_movies


def get_user_ratings(
    user_id: int,
    ratings_df: pd.DataFrame,
    movies_df: pd.DataFrame
) -> List[Dict[str, Any]]:
    """
    Get all ratings for a specific user with movie details

    Args:
        user_id: User ID to get ratings for
        ratings_df: DataFrame containing all user ratings
        movies_df: DataFrame containing movie information

    Returns:
        List of dictionaries containing user ratings with movie details

    Raises:
        ValueError: If user_id has no ratings
    """
    # Get user's ratings
    user_ratings = ratings_df[ratings_df['userId'] == user_id].copy()

    if len(user_ratings) == 0:
        raise ValueError(f"User ID {user_id} has no ratings")

    # Merge with movies to get titles and genres
    user_ratings = user_ratings.merge(movies_df, on='movieId', how='left')

    # Sort by rating (descending) and then by timestamp (most recent first)
    user_ratings = user_ratings.sort_values(['rating', 'timestamp'], ascending=[False, False])

    # Build response
    ratings_list = []
    for _, row in user_ratings.iterrows():
        ratings_list.append({
            'userId': int(row['userId']),
            'movieId': int(row['movieId']),
            'rating': float(row['rating']),
            'timestamp': int(row['timestamp']) if pd.notna(row['timestamp']) else None,
            'title': row['title'],
            'genres': row['genres']
        })

    return ratings_list
