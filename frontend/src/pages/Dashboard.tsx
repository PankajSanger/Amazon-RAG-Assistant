import { Link } from 'react-router-dom'
import { MessageSquareText, Package, Star, PackageSearch } from 'lucide-react'

import { useStats } from '@/api/hooks'
import { PageHeader } from '@/components/PageHeader'
import { StatCard } from '@/components/StatCard'
import { RatingChart } from '@/components/RatingChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

export function Dashboard() {
  const { data: stats, isLoading } = useStats()

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="An overview of your scraped Amazon catalog and RAG index."
        action={
          <Button asChild>
            <Link to="/scrape">
              <PackageSearch />
              Scrape data
            </Link>
          </Button>
        }
      />

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard label="Products scraped" value={String(stats?.product_count ?? 0)} icon={Package} />
          <StatCard
            label="Reviews scraped"
            value={String(stats?.review_count ?? 0)}
            icon={MessageSquareText}
            accent="success"
          />
          <StatCard
            label="Avg. product rating"
            value={stats?.avg_product_rating ? stats.avg_product_rating.toFixed(2) : '—'}
            icon={Star}
            accent="warning"
          />
        </div>
      )}

      <div className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Product rating distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <RatingChart distribution={stats?.rating_distribution ?? {}} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Get started</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <QuickLink
              to="/scrape"
              title="Scrape a product or keyword"
              description="Pull fresh product details and reviews from Amazon."
            />
            <QuickLink
              to="/ask/products"
              title="Ask about products"
              description="Query price, rating and ingredients with natural language."
            />
            <QuickLink
              to="/ask/reviews"
              title="Ask about reviews"
              description="Surface complaints, praise and usage feedback."
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function QuickLink({ to, title, description }: { to: string; title: string; description: string }) {
  return (
    <Link
      to={to}
      className="flex flex-col rounded-lg border border-border px-4 py-3 transition-colors hover:border-primary/40 hover:bg-accent"
    >
      <span className="text-sm font-medium text-foreground">{title}</span>
      <span className="text-xs text-muted-foreground">{description}</span>
    </Link>
  )
}
