import { Star } from 'lucide-react'

import type { ProductSource, ReviewSource } from '@/api/types'
import { Badge } from '@/components/ui/badge'

export function ProductSourceCard({ source }: { source: ProductSource }) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border bg-muted/40 px-3 py-2">
      <p className="text-sm font-medium text-foreground line-clamp-2">{source.title ?? 'Untitled product'}</p>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {source.rating != null && (
          <span className="flex items-center gap-1">
            <Star className="h-3 w-3 fill-warning text-warning" />
            {source.rating}
          </span>
        )}
        {source.no_of_ratings != null && <span>{source.no_of_ratings} ratings</span>}
        {source.price != null && <Badge variant="outline">₹{source.price}</Badge>}
      </div>
    </div>
  )
}

export function ReviewSourceCard({ source }: { source: ReviewSource }) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border bg-muted/40 px-3 py-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-foreground">{source.author ?? 'Amazon Customer'}</p>
        {source.rating != null && (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Star className="h-3 w-3 fill-warning text-warning" />
            {source.rating}
          </span>
        )}
      </div>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {source.date && <span>{source.date}</span>}
        {source.asin && <Badge variant="outline">{source.asin}</Badge>}
      </div>
    </div>
  )
}
