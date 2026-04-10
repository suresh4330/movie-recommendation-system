"""
FastAPI Backend for Movie Recommendation System

This is the main application file that defines all API endpoints
for the movie recommendation system.
"""

import pickle
import pandas as pd
import os
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import ML model classes BEFORE loading pickled models
from ml_models import HybridRecommender
import sys

# FIX: The HybridRecommender model was pickled in a script where it was defined in __main__.
# When loading via uvicorn, __main__ is uvicorn.__main__, so we need to inject the class there.
import __main__
setattr(__main__, "HybridRecommender", HybridRecommender)

from models import (
    Movie,
    MovieRecommendation,
    UserRating,
    RatingInput,
    APIInfo
)
from recommender import (
    get_recommendations_with_algorithm,
    get_similar_movies,
    get_user_ratings
)


# Global variables for models and data
models = {}
ratings = None
movies = None


def get_allowed_origins() -> List[str]:
    """
    Build the CORS allowlist from environment variables.

    Supported variables:
    - CORS_ALLOWED_ORIGINS: comma-separated list of allowed origins
    - FRONTEND_URL: single frontend origin for deployed environments
    """
    configured_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
    frontend_url = os.getenv("FRONTEND_URL", "")

    origins = [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ]

    if frontend_url.strip():
        origins.append(frontend_url.strip())

    if origins:
        return list(dict.fromkeys(origins))

    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for loading models and data on startup
    and cleaning up on shutdown
    """
    global models, ratings, movies

    base_path = Path(__file__).resolve().parent.parent

    try:
        print("🔄 Loading ML models and data...")

        # Load SVD model (requires scikit-surprise)
        try:
            with open(base_path / 'models' / 'svd_model.pkl', 'rb') as f:
                models['svd'] = pickle.load(f)
            print("  ✓ SVD model loaded")
        except Exception as e:
            print(f"  ⚠️ SVD model skipped: {str(e)}")
            print("  🔄 Falling back to Scikit-Learn SVD implementation...")
            try:
                # Import replacement model
                from ml_models import ScikitLearnSVD
                svd_model = ScikitLearnSVD(n_components=20)
                
                # We need ratings df to train
                if ratings is None:
                     ratings = pd.read_csv(base_path / 'data' / 'processed' / 'ratings_clean.csv')
                
                svd_model.fit(ratings)
                models['svd'] = svd_model
                print("  ✓ Scikit-Learn SVD model trained and loaded")
            except Exception as e2:
                print(f"  ❌ Fallback SVD failed: {str(e2)}")

        # Load Hybrid recommender (requires SVD)
        try:
            with open(base_path / 'models' / 'hybrid_recommender.pkl', 'rb') as f:
                models['hybrid'] = pickle.load(f)
            print("  ✓ Hybrid recommender loaded")
        except Exception as e:
            print(f"  ⚠️ Hybrid recommender skipped: {str(e)}")
            
            # If we have SVD replacement, we can re-create Hybrid
            if 'svd' in models:
                try:
                    print("  🔄 Re-initializing Hybrid Recommender with replacement SVD...")
                    
                    # Need content similarity matrix
                   
                    # Check if 'content_similarity_matrix.npy' exists
                    sim_path = base_path / 'models' / 'content_similarity_matrix.npy'
                    if sim_path.exists():
                        import numpy as np
                        content_sim = np.load(sim_path)
                    else:
                         # Fallback if matrix not found (less likely)
                         print("  ⚠️ Content similarity matrix not found, cannot init Hybrid")
                         raise FileNotFoundError("Sim matrix missing")

                    # We need movies df
                    if movies is None:
                        movies = pd.read_csv(base_path / 'data' / 'processed' / 'movies_clean.csv')

                    # Re-init hybrid
                    # HybridRecommender is already imported
                    from ml_models import HybridRecommender
                    
                    hybrid_model = HybridRecommender(
                        cf_model=models['svd'],
                        content_sim_matrix=content_sim,
                        movies_df=movies
                    )
                    models['hybrid'] = hybrid_model
                    print("  ✓ Hybrid Recommender re-initialized successfully")
                except Exception as e2:
                    print(f"  ❌ Fallback Hybrid init failed: {str(e2)}")


        # Load KNN User model
        try:
            with open(base_path / 'models' / 'knn_user_model.pkl', 'rb') as f:
                models['knn_user'] = pickle.load(f)
            print("  ✓ User-based KNN model loaded")
        except Exception as e:
            print(f"  ⚠️ User-based KNN model skipped: {str(e)}")

        # Load KNN Item model
        try:
            with open(base_path / 'models' / 'knn_item_model.pkl', 'rb') as f:
                models['knn_item'] = pickle.load(f)
            print("  ✓ Item-based KNN model loaded")
        except Exception as e:
            print(f"  ⚠️ Item-based KNN model skipped: {str(e)}")

        # Load data
        ratings = pd.read_csv(base_path / 'data' / 'processed' / 'ratings_clean.csv')
        print(f"  ✓ Loaded {len(ratings)} ratings")

        movies = pd.read_csv(base_path / 'data' / 'processed' / 'movies_clean.csv')
        print(f"  ✓ Loaded {len(movies)} movies")

        print("✅ Data loading complete!")

    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        raise

    yield

    # Cleanup (if needed)
    print("👋 Shutting down API...")


# Initialize FastAPI app
app = FastAPI(
    title="Movie Recommendation API",
    description="A powerful API for personalized movie recommendations using multiple ML algorithms",
    version="1.0.0",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_model=APIInfo)
async def root():
    """
    Get API information and status

    Returns basic information about the API including version,
    status, and whether models are loaded.
    """
    return APIInfo(
        name="Movie Recommendation API",
        version="1.0.0",
        status="online",
        models_loaded=len(models) == 4 and ratings is not None and movies is not None,
        description="Personalized movie recommendations using SVD, KNN, and Hybrid algorithms"
    )


@app.get("/recommendations/{user_id}", response_model=List[MovieRecommendation])
async def get_recommendations(
    user_id: int = PathParam(..., ge=1, description="User ID to generate recommendations for"),
    n: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    algorithm: str = Query(
        "svd",
        pattern="^(svd|hybrid|user-knn|item-knn)$",
        description="Algorithm to use for recommendations"
    )
):
    """
    Get personalized movie recommendations for a user

    Returns a list of recommended movies with predicted ratings based on
    the specified algorithm.

    **Algorithms:**
    - `svd`: Singular Value Decomposition (matrix factorization)
    - `hybrid`: Combination of collaborative and content-based filtering
    - `user-knn`: User-based K-Nearest Neighbors
    - `item-knn`: Item-based K-Nearest Neighbors

    **Example:**
    ```
    GET /recommendations/1?n=20&algorithm=svd
    ```
    """
    try:
        # Check if user exists
        if user_id not in ratings['userId'].values:
            raise HTTPException(
                status_code=404,
                detail=f"User ID {user_id} not found. Please provide a valid user ID."
            )

        # Generate recommendations
        recommendations = get_recommendations_with_algorithm(
            user_id=user_id,
            algorithm=algorithm,
            n=n,
            ratings_df=ratings,
            movies_df=movies,
            models=models
        )

        return recommendations

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


@app.get("/movies/", response_model=List[Movie])
async def get_movies(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of movies to return"),
    genre: Optional[str] = Query(None, description="Filter by genre (e.g., 'Action', 'Drama')")
):
    """
    Get a list of movies from the catalog

    Returns movies with optional genre filtering. Results are limited
    to prevent large responses.

    **Example:**
    ```
    GET /movies/?limit=20&genre=Action
    ```
    """
    try:
        filtered_movies = movies.copy()

        # Apply genre filter if provided
        if genre:
            filtered_movies = filtered_movies[
                filtered_movies['genres'].str.contains(genre, case=False, na=False)
            ]

            if len(filtered_movies) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No movies found with genre: {genre}"
                )

        # Limit results
        filtered_movies = filtered_movies.head(limit)

        # Convert to response format
        movies_list = []
        for _, row in filtered_movies.iterrows():
            movies_list.append({
                'movieId': int(row['movieId']),
                'title': row['title'],
                'genres': row['genres']
            })

        return movies_list

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving movies: {str(e)}"
        )


@app.get("/movies/{movie_id}", response_model=Movie)
async def get_movie(
    movie_id: int = PathParam(..., ge=1, description="Movie ID to retrieve")
):
    """
    Get details for a specific movie

    Returns complete information about a single movie including
    title and genres.

    **Example:**
    ```
    GET /movies/1
    ```
    """
    try:
        movie = movies[movies['movieId'] == movie_id]

        if len(movie) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Movie ID {movie_id} not found"
            )

        movie_data = movie.iloc[0]

        return Movie(
            movieId=int(movie_data['movieId']),
            title=movie_data['title'],
            genres=movie_data['genres']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving movie: {str(e)}"
        )


@app.get("/similar/{movie_id}", response_model=List[dict])
async def get_similar(
    movie_id: int = PathParam(..., ge=1, description="Movie ID to find similar movies for"),
    n: int = Query(10, ge=1, le=50, description="Number of similar movies to return")
):
    """
    Get movies similar to a given movie

    Uses content-based filtering (genre similarity) to find
    movies that are similar to the specified movie.

    **Example:**
    ```
    GET /similar/1?n=10
    ```
    """
    try:
        similar_movies_list = get_similar_movies(
            movie_id=movie_id,
            n=n,
            movies_df=movies
        )

        return similar_movies_list

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error finding similar movies: {str(e)}"
        )


@app.get("/user/{user_id}/ratings", response_model=List[UserRating])
async def get_user_ratings_endpoint(
    user_id: int = PathParam(..., ge=1, description="User ID to get ratings for")
):
    """
    Get all ratings for a specific user

    Returns the complete rating history for a user, including
    movie details and timestamps.

    **Example:**
    ```
    GET /user/1/ratings
    ```
    """
    try:
        user_ratings_list = get_user_ratings(
            user_id=user_id,
            ratings_df=ratings,
            movies_df=movies
        )

        return user_ratings_list

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user ratings: {str(e)}"
        )


@app.post("/ratings", response_model=dict)
async def create_rating(rating_input: RatingInput):
    """
    Submit a new movie rating

    Accepts a new rating from a user. Note: This endpoint currently
    only validates and returns success. In a production system, this
    would store the rating and potentially trigger model retraining.

    **Request Body:**
    ```json
    {
        "userId": 1,
        "movieId": 318,
        "rating": 4.5
    }
    ```
    """
    try:
        # Validate that the movie exists
        if rating_input.movieId not in movies['movieId'].values:
            raise HTTPException(
                status_code=404,
                detail=f"Movie ID {rating_input.movieId} not found"
            )

        # In a real application, you would:
        # 1. Store the rating in the database
        # 2. Update the ratings dataframe
        # 3. Optionally trigger model retraining

        movie_title = movies[movies['movieId'] == rating_input.movieId].iloc[0]['title']

        return {
            "success": True,
            "message": f"Rating submitted successfully for '{movie_title}'",
            "userId": rating_input.userId,
            "movieId": rating_input.movieId,
            "rating": rating_input.rating
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting rating: {str(e)}"
        )


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring

    Returns the health status of the API and all loaded components.
    """
    return {
        "status": "healthy",
        "models": {
            "svd": "svd" in models,
            "hybrid": "hybrid" in models,
            "knn_user": "knn_user" in models,
            "knn_item": "knn_item" in models
        },
        "data": {
            "ratings_loaded": ratings is not None,
            "movies_loaded": movies is not None,
            "num_ratings": len(ratings) if ratings is not None else 0,
            "num_movies": len(movies) if movies is not None else 0
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
