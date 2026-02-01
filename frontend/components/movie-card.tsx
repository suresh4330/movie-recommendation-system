import { Star } from 'lucide-react'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatGenres, formatRating } from '@/lib/utils'
import type { Recommendation, Movie } from '@/types'

interface MovieCardProps {
  movie: Recommendation | Movie
  rank?: number
  onViewDetails?: () => void
}

export default function MovieCard({ movie, rank, onViewDetails }: MovieCardProps) {
  const genres = formatGenres(movie.genres)
  const isPrediction = 'predicted_rating' in movie

  return (
    <Card className="flex flex-col h-full hover:shadow-lg transition-shadow">
      <CardContent className="flex-1 p-6">
        {/* Rank Badge */}
        {rank && (
          <Badge className="mb-3 text-sm font-bold">
            #{rank}
          </Badge>
        )}

        {/* Movie Title */}
        <h3 className="font-semibold text-lg mb-3 line-clamp-2">
          {movie.title}
        </h3>

        {/* Genres */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {genres.slice(0, 3).map((genre, index) => (
            <Badge key={index} variant="secondary" className="text-xs">
              {genre}
            </Badge>
          ))}
          {genres.length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{genres.length - 3}
            </Badge>
          )}
        </div>

        {/* Rating */}
        {isPrediction && (
          <div className="flex items-center space-x-1 text-muted-foreground">
            <Star className="h-4 w-4 fill-current" />
            <span className="font-semibold">
              {formatRating(movie.predicted_rating)}
            </span>
          </div>
        )}
      </CardContent>

      {/* Actions */}
      {onViewDetails && (
        <CardFooter className="p-6 pt-0">
          <Button
            onClick={onViewDetails}
            variant="outline"
            className="w-full"
          >
            More Info
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}
