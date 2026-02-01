'use client'

import { useState } from 'react'
import { User, BarChart3, Star, Film, Loader2, AlertCircle, Clock } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { movieAPI } from '@/lib/api'
import { formatGenres, formatRating, formatTimestamp } from '@/lib/utils'
import type { UserRating } from '@/types'

export default function ProfilePage() {
  const [userId, setUserId] = useState('')
  const [ratings, setRatings] = useState<UserRating[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleLoadProfile = async () => {
    const userIdNum = parseInt(userId)
    if (isNaN(userIdNum) || userIdNum < 1) {
      setError('Please enter a valid user ID (positive number)')
      return
    }

    setLoading(true)
    setError(null)
    setRatings([])

    try {
      const data = await movieAPI.getUserRatings(userIdNum)
      setRatings(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load user profile')
    } finally {
      setLoading(false)
    }
  }

  // Calculate statistics
  const totalRatings = ratings.length
  const avgRating = totalRatings > 0
    ? ratings.reduce((sum, r) => sum + r.rating, 0) / totalRatings
    : 0
  const uniqueGenres = new Set(
    ratings.flatMap((r) => formatGenres(r.genres))
  ).size

  const topRated = [...ratings]
    .sort((a, b) => b.rating - a.rating)
    .slice(0, 5)

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-2 flex items-center justify-center space-x-2">
          <User className="h-8 w-8" />
          <span>User Profile</span>
        </h1>
        <p className="text-muted-foreground">
          View your rating history and statistics
        </p>
      </div>

      {/* User ID Input */}
      <Card className="mb-8 max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Load User Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-4">
            <Input
              type="number"
              placeholder="Enter user ID"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              min="1"
            />
            <Button onClick={handleLoadProfile} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Loading...
                </>
              ) : (
                'Load Profile'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-8 max-w-2xl mx-auto">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Statistics */}
      {!loading && ratings.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 max-w-4xl mx-auto">
            {/* Total Ratings */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <BarChart3 className="h-8 w-8 text-muted-foreground" />
                  <div>
                    <p className="text-3xl font-bold">{totalRatings}</p>
                    <p className="text-sm text-muted-foreground">Total Ratings</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Average Rating */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <Star className="h-8 w-8 text-muted-foreground fill-current" />
                  <div>
                    <p className="text-3xl font-bold">{formatRating(avgRating)}</p>
                    <p className="text-sm text-muted-foreground">Avg Rating</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Unique Genres */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <Film className="h-8 w-8 text-muted-foreground" />
                  <div>
                    <p className="text-3xl font-bold">{uniqueGenres}</p>
                    <p className="text-sm text-muted-foreground">Genres Rated</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Top Rated Movies */}
          {topRated.length > 0 && (
            <Card className="mb-8 max-w-4xl mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Star className="h-5 w-5 fill-current" />
                  <span>Top Rated Movies</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {topRated.map((rating, index) => (
                    <div
                      key={rating.movieId}
                      className="flex items-start space-x-4 p-4 rounded-lg border hover:bg-accent transition-colors"
                    >
                      <div className="flex-shrink-0 w-8 text-center font-bold text-muted-foreground">
                        #{index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold mb-1">{rating.title}</h4>
                        <div className="flex flex-wrap gap-1.5">
                          {formatGenres(rating.genres).slice(0, 3).map((genre, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">
                              {genre}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="flex items-center space-x-1 flex-shrink-0">
                        <Star className="h-4 w-4 fill-current" />
                        <span className="font-bold">{formatRating(rating.rating)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Rating History */}
          <Card className="max-w-4xl mx-auto">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Clock className="h-5 w-5" />
                <span>Rating History ({ratings.length} ratings)</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {ratings.map((rating) => (
                  <div
                    key={`${rating.movieId}-${rating.timestamp}`}
                    className="flex items-start space-x-4 p-3 rounded-lg border hover:bg-accent transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium mb-1">{rating.title}</h4>
                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {formatGenres(rating.genres).slice(0, 3).map((genre, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {genre}
                          </Badge>
                        ))}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Rated: {formatTimestamp(rating.timestamp)}
                      </p>
                    </div>
                    <div className="flex items-center space-x-1 flex-shrink-0">
                      <Star className="h-4 w-4 fill-current" />
                      <span className="font-semibold">{formatRating(rating.rating)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Loading State */}
      {loading && (
        <div className="space-y-4 max-w-4xl mx-auto">
          <div className="grid grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-lg" />
            ))}
          </div>
          <Skeleton className="h-64 rounded-lg" />
          <Skeleton className="h-96 rounded-lg" />
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && ratings.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <p>Enter a user ID and click &quot;Load Profile&quot; to view rating history</p>
        </div>
      )}
    </div>
  )
}
