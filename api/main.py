"""
FastAPI backend for the movie recommendation system.

This module defines the application lifecycle, startup model loading,
deployment-safe CORS behavior, and all API endpoints.
"""

import __main__
import os
import pickle
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Path as PathParam, Query
from fastapi.middleware.cors import CORSMiddleware

from ml_models import HybridRecommender
from models import APIInfo, Movie, MovieRecommendation, RatingInput, UserRating
from recommender import (
    get_recommendations_with_algorithm,
    get_similar_movies,
    get_user_ratings,
)

# The hybrid recommender was pickled from a __main__ module in training scripts.
# When running with uvicorn, we need the class to exist on __main__ for unpickling.
setattr(__main__, "HybridRecommender", HybridRecommender)


models = {}
ratings = None
movies = None

ALGORITHM_MODEL_KEYS = {
    "svd": "svd",
    "hybrid": "hybrid",
    "user-knn": "knn_user",
    "item-knn": "knn_item",
}


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


def get_available_algorithms() -> List[str]:
    """Return the algorithms that are currently loaded and usable."""
    return [
        algorithm
        for algorithm, model_key in ALGORITHM_MODEL_KEYS.items()
        if model_key in models
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load data and recover any deployable fallback models on startup.
    """
    del app
    global models, ratings, movies

    base_path = Path(__file__).resolve().parent.parent
    models.clear()
    ratings = None
    movies = None

    try:
        print("Loading ML models and data...")

        ratings = pd.read_csv(base_path / "data" / "processed" / "ratings_clean.csv")
        print(f"  Loaded {len(ratings)} ratings")

        movies = pd.read_csv(base_path / "data" / "processed" / "movies_clean.csv")
        print(f"  Loaded {len(movies)} movies")

        try:
            with open(base_path / "models" / "svd_model.pkl", "rb") as file_handle:
                models["svd"] = pickle.load(file_handle)
            print("  Loaded SVD model")
        except Exception as exc:
            print(f"  SVD model unavailable: {exc}")
            print("  Falling back to Scikit-Learn SVD...")
            try:
                from ml_models import ScikitLearnSVD

                svd_model = ScikitLearnSVD(n_components=20)
                svd_model.fit(ratings)
                models["svd"] = svd_model
                print("  Built Scikit-Learn SVD fallback")
            except Exception as fallback_exc:
                print(f"  SVD fallback failed: {fallback_exc}")

        # Always build the hybrid recommender at startup from SVD + content similarity.
        # The precomputed hybrid_recommender.pkl (~762 MB) is too large for cloud
        # deployments (Render, Railway, etc.), so we rebuild it in ~1-2 seconds instead.
        if "svd" in models:
            try:
                # Use the new memory-efficient genre matrix builder
                from ml_models import build_genre_matrix
                genre_matrix = build_genre_matrix(movies)
                print("  Built sparse genre matrix (memory optimized)")

                models["hybrid"] = HybridRecommender(
                    cf_model=models["svd"],
                    genre_matrix=genre_matrix,
                    movies_df=movies,
                )
                print("  Built hybrid recommender (Optimized for Render Free Tier)")
            except Exception as exc:
                print(f"  Hybrid recommender build failed: {exc}")
        else:
            print("  Skipping hybrid recommender (SVD not loaded)")

        try:
            with open(base_path / "models" / "knn_user_model.pkl", "rb") as file_handle:
                models["knn_user"] = pickle.load(file_handle)
            print("  Loaded user-based KNN model")
        except Exception as exc:
            print(f"  User-based KNN unavailable: {exc}")
            print("  Falling back to Scikit-Learn user-based KNN...")
            try:
                from ml_models import ScikitLearnKNN

                knn_user_model = ScikitLearnKNN(user_based=True)
                knn_user_model.fit(ratings)
                models["knn_user"] = knn_user_model
                print("  Built user-based KNN fallback")
            except Exception as fallback_exc:
                print(f"  User-based KNN fallback failed: {fallback_exc}")

        try:
            with open(base_path / "models" / "knn_item_model.pkl", "rb") as file_handle:
                models["knn_item"] = pickle.load(file_handle)
            print("  Loaded item-based KNN model")
        except Exception as exc:
            print(f"  Item-based KNN unavailable: {exc}")
            print("  Falling back to Scikit-Learn item-based KNN...")
            try:
                from ml_models import ScikitLearnKNN

                knn_item_model = ScikitLearnKNN(user_based=False)
                knn_item_model.fit(ratings)
                models["knn_item"] = knn_item_model
                print("  Built item-based KNN fallback")
            except Exception as fallback_exc:
                print(f"  Item-based KNN fallback failed: {fallback_exc}")

        print("Data loading complete")
        print(f"Available algorithms: {', '.join(get_available_algorithms()) or 'none'}")

    except Exception as exc:
        print(f"Error loading data: {exc}")
        raise

    yield

    print("Shutting down API...")


app = FastAPI(
    title="Movie Recommendation API",
    description="A powerful API for personalized movie recommendations using multiple ML algorithms",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=APIInfo)
async def root():
    """
    Get API information and startup status.
    """
    return APIInfo(
        name="Movie Recommendation API",
        version="1.0.0",
        status="online",
        models_loaded=bool(get_available_algorithms()) and ratings is not None and movies is not None,
        available_algorithms=get_available_algorithms(),
        description="Personalized movie recommendations using SVD, KNN, and Hybrid algorithms",
    )


@app.get("/recommendations/{user_id}", response_model=List[MovieRecommendation])
async def get_recommendations(
    user_id: int = PathParam(..., ge=1, description="User ID to generate recommendations for"),
    n: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    algorithm: str = Query(
        "svd",
        pattern="^(svd|hybrid|user-knn|item-knn)$",
        description="Algorithm to use for recommendations",
    ),
):
    """
    Get personalized movie recommendations for a user.
    """
    try:
        available_algorithms = get_available_algorithms()
        if algorithm not in available_algorithms:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Algorithm '{algorithm}' is not available in this deployment. "
                    f"Available algorithms: {', '.join(available_algorithms) or 'none'}."
                ),
            )

        if ratings is None or movies is None:
            raise HTTPException(
                status_code=503,
                detail="Recommendation data is still loading. Please try again in a moment.",
            )

        if user_id not in ratings["userId"].values:
            raise HTTPException(
                status_code=404,
                detail=f"User ID {user_id} not found. Please provide a valid user ID.",
            )

        return get_recommendations_with_algorithm(
            user_id=user_id,
            algorithm=algorithm,
            n=n,
            ratings_df=ratings,
            movies_df=movies,
            models=models,
        )

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Algorithm assets are unavailable for this deployment: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {exc}",
        )


@app.get("/movies/", response_model=List[Movie])
async def get_movies(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of movies to return"),
    genre: Optional[str] = Query(None, description="Filter by genre (e.g., 'Action', 'Drama')"),
):
    """
    Get a list of movies from the catalog.
    """
    try:
        filtered_movies = movies.copy()

        if genre:
            filtered_movies = filtered_movies[
                filtered_movies["genres"].str.contains(genre, case=False, na=False)
            ]

            if len(filtered_movies) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No movies found with genre: {genre}",
                )

        filtered_movies = filtered_movies.head(limit)

        movies_list = []
        for _, row in filtered_movies.iterrows():
            movies_list.append(
                {
                    "movieId": int(row["movieId"]),
                    "title": row["title"],
                    "genres": row["genres"],
                }
            )

        return movies_list

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving movies: {exc}",
        )


@app.get("/movies/{movie_id}", response_model=Movie)
async def get_movie(
    movie_id: int = PathParam(..., ge=1, description="Movie ID to retrieve"),
):
    """
    Get details for a specific movie.
    """
    try:
        movie = movies[movies["movieId"] == movie_id]

        if len(movie) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Movie ID {movie_id} not found",
            )

        movie_data = movie.iloc[0]

        return Movie(
            movieId=int(movie_data["movieId"]),
            title=movie_data["title"],
            genres=movie_data["genres"],
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving movie: {exc}",
        )


@app.get("/similar/{movie_id}", response_model=List[dict])
async def get_similar(
    movie_id: int = PathParam(..., ge=1, description="Movie ID to find similar movies for"),
    n: int = Query(10, ge=1, le=50, description="Number of similar movies to return"),
):
    """
    Get movies similar to a given movie.
    """
    try:
        return get_similar_movies(
            movie_id=movie_id,
            n=n,
            movies_df=movies,
        )

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error finding similar movies: {exc}",
        )


@app.get("/user/{user_id}/ratings", response_model=List[UserRating])
async def get_user_ratings_endpoint(
    user_id: int = PathParam(..., ge=1, description="User ID to get ratings for"),
):
    """
    Get all ratings for a specific user.
    """
    try:
        return get_user_ratings(
            user_id=user_id,
            ratings_df=ratings,
            movies_df=movies,
        )

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user ratings: {exc}",
        )


@app.post("/ratings", response_model=dict)
async def create_rating(rating_input: RatingInput):
    """
    Submit a new movie rating.
    """
    try:
        if rating_input.movieId not in movies["movieId"].values:
            raise HTTPException(
                status_code=404,
                detail=f"Movie ID {rating_input.movieId} not found",
            )

        movie_title = movies[movies["movieId"] == rating_input.movieId].iloc[0]["title"]

        return {
            "success": True,
            "message": f"Rating submitted successfully for '{movie_title}'",
            "userId": rating_input.userId,
            "movieId": rating_input.movieId,
            "rating": rating_input.rating,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting rating: {exc}",
        )


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "available_algorithms": get_available_algorithms(),
        "models": {
            "svd": "svd" in models,
            "hybrid": "hybrid" in models,
            "knn_user": "knn_user" in models,
            "knn_item": "knn_item" in models,
        },
        "data": {
            "ratings_loaded": ratings is not None,
            "movies_loaded": movies is not None,
            "num_ratings": len(ratings) if ratings is not None else 0,
            "num_movies": len(movies) if movies is not None else 0,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
