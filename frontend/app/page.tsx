'use client'

import { useState } from 'react'
import { Sparkles, TrendingUp, Loader2, AlertCircle } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import MovieCard from '@/components/movie-card'
import MovieDetailsModal from '@/components/movie-details-modal'
import { movieAPI } from '@/lib/api'
import type { Recommendation, Algorithm } from '@/types'

const ALGORITHMS: { value: Algorithm; label: string }[] = [
  { value: 'svd', label: 'SVD (Matrix Factorization)' },
  { value: 'hybrid', label: 'Hybrid (CF + Content)' },
  { value: 'user-knn', label: 'User-based KNN' },
  { value: 'item-knn', label: 'Item-based KNN' },
]

const COUNTS = [10, 20, 30, 40, 50]

export default function HomePage() {
  const [userId, setUserId] = useState('')
  const [algorithm, setAlgorithm] = useState<Algorithm>('svd')
  const [count, setCount] = useState(20)
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedMovieId, setSelectedMovieId] = useState<number | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const handleGetRecommendations = async () => {
    const userIdNum = parseInt(userId)
    if (isNaN(userIdNum) || userIdNum < 1) {
      setError('Please enter a valid user ID (positive number)')
      return
    }

    setLoading(true)
    setError(null)
    setRecommendations([])

    try {
      const data = await movieAPI.getRecommendations(userIdNum, algorithm, count)
      setRecommendations(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load recommendations')
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetails = (movieId: number) => {
    setSelectedMovieId(movieId)
    setModalOpen(true)
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-2 flex items-center justify-center space-x-2">
          <Sparkles className="h-8 w-8" />
          <span>Get Personalized Recommendations</span>
        </h1>
        <p className="text-muted-foreground">
          Choose your preferred algorithm and discover movies you&apos;ll love
        </p>
      </div>

      {/* Recommendation Form */}
      <Card className="mb-8 max-w-3xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5" />
            <span>Recommendation Parameters</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* User ID */}
            <div className="space-y-2">
              <label className="text-sm font-medium">User ID</label>
              <Input
                type="number"
                placeholder="Enter user ID"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                min="1"
              />
            </div>

            {/* Algorithm */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Algorithm</label>
              <Select
                value={algorithm}
                onValueChange={(value) => setAlgorithm(value as Algorithm)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ALGORITHMS.map((algo) => (
                    <SelectItem key={algo.value} value={algo.value}>
                      {algo.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Count */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Number of Results</label>
              <Select
                value={count.toString()}
                onValueChange={(value) => setCount(parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {COUNTS.map((c) => (
                    <SelectItem key={c} value={c.toString()}>
                      {c} movies
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            onClick={handleGetRecommendations}
            className="w-full mt-6"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Loading Recommendations...
              </>
            ) : (
              'Get Recommendations'
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-8 max-w-3xl mx-auto">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading Skeletons */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-64 rounded-lg" />
          ))}
        </div>
      )}

      {/* Results */}
      {!loading && recommendations.length > 0 && (
        <>
          <div className="mb-6 text-center">
            <h2 className="text-2xl font-bold">
              🎯 Top {recommendations.length} Recommendations for You
            </h2>
            <p className="text-muted-foreground">
              Using {ALGORITHMS.find((a) => a.value === algorithm)?.label}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {recommendations.map((movie, index) => (
              <MovieCard
                key={movie.movieId}
                movie={movie}
                rank={index + 1}
                onViewDetails={() => handleViewDetails(movie.movieId)}
              />
            ))}
          </div>
        </>
      )}

      {/* Empty State */}
      {!loading && !error && recommendations.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <p>Enter a user ID and click &quot;Get Recommendations&quot; to start</p>
        </div>
      )}

      {/* Movie Details Modal */}
      <MovieDetailsModal
        movieId={selectedMovieId}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </div>
  )
}
