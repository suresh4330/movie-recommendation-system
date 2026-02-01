import axios from 'axios'
import type { Movie, Recommendation, UserRating, SimilarMovie, APIInfo } from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const movieAPI = {
  /**
   * Get personalized movie recommendations for a user
   */
  getRecommendations: async (
    userId: number,
    algorithm: string = 'svd',
    n: number = 20
  ): Promise<Recommendation[]> => {
    const response = await api.get(`/recommendations/${userId}`, {
      params: { algorithm, n },
    })
    return response.data
  },

  /**
   * Get a list of movies with optional filters
   */
  getMovies: async (limit: number = 50, genre?: string): Promise<Movie[]> => {
    const response = await api.get('/movies/', {
      params: { limit, ...(genre && { genre }) },
    })
    return response.data
  },

  /**
   * Get details for a specific movie
   */
  getMovie: async (movieId: number): Promise<Movie> => {
    const response = await api.get(`/movies/${movieId}`)
    return response.data
  },

  /**
   * Get movies similar to a given movie
   */
  getSimilarMovies: async (movieId: number, n: number = 10): Promise<SimilarMovie[]> => {
    const response = await api.get(`/similar/${movieId}`, {
      params: { n },
    })
    return response.data
  },

  /**
   * Get all ratings for a specific user
   */
  getUserRatings: async (userId: number): Promise<UserRating[]> => {
    const response = await api.get(`/user/${userId}/ratings`)
    return response.data
  },

  /**
   * Submit a new movie rating
   */
  submitRating: async (userId: number, movieId: number, rating: number): Promise<any> => {
    const response = await api.post('/ratings', {
      userId,
      movieId,
      rating,
    })
    return response.data
  },

  /**
   * Get API information and status
   */
  getAPIInfo: async (): Promise<APIInfo> => {
    const response = await api.get('/')
    return response.data
  },

  /**
   * Get API health status
   */
  getHealth: async (): Promise<any> => {
    const response = await api.get('/health')
    return response.data
  },
}
