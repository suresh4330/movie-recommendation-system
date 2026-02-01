'use client'

import { useState, useEffect } from 'react'
import { Film, Loader2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { movieAPI } from '@/lib/api'
import { formatGenres } from '@/lib/utils'
import type { Movie, SimilarMovie } from '@/types'

interface MovieDetailsModalProps {
  movieId: number | null
  isOpen: boolean
  onClose: () => void
}

export default function MovieDetailsModal({
  movieId,
  isOpen,
  onClose,
}: MovieDetailsModalProps) {
  const [movie, setMovie] = useState<Movie | null>(null)
  const [similarMovies, setSimilarMovies] = useState<SimilarMovie[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (movieId && isOpen) {
      fetchMovieDetails()
    }
  }, [movieId, isOpen])

  const fetchMovieDetails = async () => {
    if (!movieId) return

    setLoading(true)
    setError(null)

    try {
      const [movieData, similarData] = await Promise.all([
        movieAPI.getMovie(movieId),
        movieAPI.getSimilarMovies(movieId, 5),
      ])

      setMovie(movieData)
      setSimilarMovies(similarData)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load movie details')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {movie && !loading && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2 text-2xl">
                <Film className="h-6 w-6" />
                <span>{movie.title}</span>
              </DialogTitle>
            </DialogHeader>

            <div className="space-y-6">
              {/* Genres */}
              <div>
                <h3 className="text-sm font-semibold mb-2 text-muted-foreground">
                  Genres
                </h3>
                <div className="flex flex-wrap gap-2">
                  {formatGenres(movie.genres).map((genre, index) => (
                    <Badge key={index} variant="secondary">
                      {genre}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Similar Movies */}
              {similarMovies.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold mb-3 text-muted-foreground">
                    Similar Movies
                  </h3>
                  <div className="space-y-2">
                    {similarMovies.map((similar) => (
                      <div
                        key={similar.movieId}
                        className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-accent transition-colors"
                      >
                        <Film className="h-5 w-5 mt-0.5 flex-shrink-0 text-muted-foreground" />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm line-clamp-1">
                            {similar.title}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {similar.genres}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
