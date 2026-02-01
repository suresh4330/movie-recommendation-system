"""
Pydantic models for the Movie Recommendation API

This module defines the data models used for request/response validation
and serialization in the FastAPI application.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Movie(BaseModel):
    """
    Represents a movie in the catalog

    Attributes:
        movieId: Unique identifier for the movie
        title: Movie title including year
        genres: Pipe-separated list of genres
    """
    movieId: int = Field(..., description="Unique movie identifier")
    title: str = Field(..., description="Movie title with year")
    genres: str = Field(..., description="Pipe-separated genres")


class MovieRecommendation(BaseModel):
    """
    Represents a movie recommendation with predicted rating

    Attributes:
        movieId: Unique identifier for the movie
        title: Movie title including year
        genres: Pipe-separated list of genres
        predicted_rating: Predicted rating for the user (0-5 scale)
    """
    movieId: int = Field(..., description="Unique movie identifier")
    title: str = Field(..., description="Movie title with year")
    genres: str = Field(..., description="Pipe-separated genres")
    predicted_rating: float = Field(..., ge=0, le=5, description="Predicted rating (0-5)")


class UserRating(BaseModel):
    """
    Represents a user's rating of a movie

    Attributes:
        userId: User identifier
        movieId: Movie identifier
        rating: Rating value (0.5 to 5.0)
        timestamp: Unix timestamp of when rating was created
        title: Movie title (optional, for display purposes)
        genres: Movie genres (optional, for display purposes)
    """
    userId: int = Field(..., description="User identifier")
    movieId: int = Field(..., description="Movie identifier")
    rating: float = Field(..., ge=0.5, le=5.0, description="Rating value (0.5-5.0)")
    timestamp: Optional[int] = Field(None, description="Unix timestamp")
    title: Optional[str] = Field(None, description="Movie title")
    genres: Optional[str] = Field(None, description="Movie genres")


class RatingInput(BaseModel):
    """
    Input model for creating a new rating

    Attributes:
        userId: User identifier
        movieId: Movie identifier
        rating: Rating value (0.5 to 5.0)
    """
    userId: int = Field(..., description="User identifier", gt=0)
    movieId: int = Field(..., description="Movie identifier", gt=0)
    rating: float = Field(..., ge=0.5, le=5.0, description="Rating value (0.5-5.0)")


class APIInfo(BaseModel):
    """
    API information and status

    Attributes:
        name: API name
        version: API version
        status: Current status
        models_loaded: Whether ML models are loaded
        description: API description
    """
    name: str
    version: str
    status: str
    models_loaded: bool
    description: str
