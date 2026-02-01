'use client'

import { useState, useEffect } from 'react'
import { Search as SearchIcon, Film, Loader2, AlertCircle } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import MovieDetailsModal from '@/components/movie-details-modal'
import { movieAPI } from '@/lib/api'
import { formatGenres } from '@/lib/utils'
import type { Movie } from '@/types'

const GENRES = [
  'All Genres',
  'Action',
  'Adventure',
  'Animation',
  'Children',
  'Comedy',
  'Crime',
  'Documentary',
  'Drama',
  'Fantasy',
  'Film-Noir',
  'Horror',
  'Musical',
  'Mystery',
  'Romance',
  'Sci-Fi',
  'Thriller',
  'War',
  'Western',
]

const LIMITS = [25, 50, 75, 100]

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedGenre, setSelectedGenre] = useState('All Genres')
  const [limit, setLimit] = useState(50)
  const [movies, setMovies] = useState<Movie[]>([])
  const [filteredMovies, setFilteredMovies] = useState<Movie[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedMovieId, setSelectedMovieId] = useState<number | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  useEffect(() => {
    loadMovies()
  }, [selectedGenre, limit])

  useEffect(() => {
    filterMovies()
  }, [searchQuery, movies])

  const loadMovies = async () => {
    setLoading(true)
    setError(null)

    try {
      const genre = selectedGenre === 'All Genres' ? undefined : selectedGenre
      const data = await movieAPI.getMovies(limit, genre)
      setMovies(data)
      setFilteredMovies(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load movies')
      setMovies([])
      setFilteredMovies([])
    } finally {
      setLoading(false)
    }
  }

  const filterMovies = () => {
    if (!searchQuery.trim()) {
      setFilteredMovies(movies)
      return
    }

    const query = searchQuery.toLowerCase()
    const filtered = movies.filter((movie) =>
      movie.title.toLowerCase().includes(query)
    )
    setFilteredMovies(filtered)
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
          <SearchIcon className="h-8 w-8" />
          <span>Browse Movies</span>
        </h1>
        <p className="text-muted-foreground">
          Search and filter through our movie catalog
        </p>
      </div>

      {/* Search & Filters */}
      <Card className="mb-8 max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle>Search & Filter</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search Input */}
            <div className="md:col-span-3 space-y-2">
              <label className="text-sm font-medium">Search by Title</label>
              <div className="relative">
                <SearchIcon className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search movies..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Genre Filter */}
            <div className="md:col-span-2 space-y-2">
              <label className="text-sm font-medium">Genre</label>
              <Select value={selectedGenre} onValueChange={setSelectedGenre}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {GENRES.map((genre) => (
                    <SelectItem key={genre} value={genre}>
                      {genre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Limit */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Results</label>
              <Select
                value={limit.toString()}
                onValueChange={(value) => setLimit(parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LIMITS.map((l) => (
                    <SelectItem key={l} value={l.toString()}>
                      {l} movies
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-8 max-w-4xl mx-auto">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Results Count */}
      {!loading && filteredMovies.length > 0 && (
        <div className="mb-6 text-center">
          <p className="text-lg font-semibold">
            📊 {filteredMovies.length} {filteredMovies.length === 1 ? 'Movie' : 'Movies'} Found
          </p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="space-y-4 max-w-4xl mx-auto">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>
      )}

      {/* Movies List */}
      {!loading && filteredMovies.length > 0 && (
        <div className="space-y-4 max-w-4xl mx-auto">
          {filteredMovies.map((movie) => (
            <Card key={movie.movieId} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                  <Film className="h-6 w-6 mt-1 flex-shrink-0 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-lg mb-2">
                      {movie.title}
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                      {formatGenres(movie.genres).map((genre, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {genre}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Button
                    onClick={() => handleViewDetails(movie.movieId)}
                    variant="outline"
                    size="sm"
                  >
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredMovies.length === 0 && !error && (
        <div className="text-center py-12 text-muted-foreground">
          <p>No movies found matching your criteria</p>
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
