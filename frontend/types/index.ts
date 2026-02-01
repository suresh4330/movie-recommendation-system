export interface Movie {
  movieId: number
  title: string
  genres: string
}

export interface Recommendation extends Movie {
  predicted_rating: number
}

export interface UserRating extends Movie {
  userId: number
  movieId: number
  rating: number
  timestamp?: number
}

export interface SimilarMovie extends Movie {
  similarity_score: number
}

export interface APIInfo {
  name: string
  version: string
  status: string
  models_loaded: boolean
  description: string
}

export type Algorithm = 'svd' | 'hybrid' | 'user-knn' | 'item-knn'

export interface RecommendationParams {
  userId: number
  algorithm: Algorithm
  n: number
}
