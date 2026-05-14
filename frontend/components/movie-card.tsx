import { Star } from 'lucide-react'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { motion } from 'framer-motion'
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
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.05 }}
      className="h-full"
    >
      <Card className="flex flex-col h-full hover:shadow-2xl transition-all duration-300 bg-white/5 backdrop-blur-lg border-white/10 text-white overflow-hidden hover:border-white/20">
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
    </motion.div>
  )
}
