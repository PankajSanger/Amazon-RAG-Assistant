import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { ExternalLink, MessageSquareText, Package, PackageSearch, Sparkles, Star } from 'lucide-react'

import { useProducts, useReviews, useStats } from '@/api/hooks'
import { PageHeader } from '@/components/PageHeader'
import { StatCard } from '@/components/StatCard'
import { RatingChart } from '@/components/RatingChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

export function Dashboard() {
  const { data: stats, isLoading } = useStats()
  const { data: products } = useProducts()
  const { data: reviews } = useReviews()

  const latestProducts = useMemo(() => [...(products ?? [])].slice(-5).reverse(), [products])

  const reviewDistribution = useMemo(() => {
    const dist: Record<string, number> = { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 }
    for (const r of reviews ?? []) {
      if (r.rating == null) continue
      const bucket = String(Math.min(5, Math.max(1, Math.round(r.rating))))
      dist[bucket] += 1
    }
    return dist
  }, [reviews])

  const isEmpty = !isLoading && stats?.product_count === 0 && stats?.review_count === 0

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

      {isEmpty ? (
        <EmptyState />
      ) : (
        <>
          {isLoading ? (
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
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
              <StatCard
                label="Avg. review rating"
                value={stats?.avg_review_rating ? stats.avg_review_rating.toFixed(2) : '—'}
                icon={Star}
                accent="warning"
              />
            </div>
          )}

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
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
                <CardTitle>Review rating distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <RatingChart distribution={reviewDistribution} />
              </CardContent>
            </Card>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Latest products</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-1">
                {latestProducts.length === 0 ? (
                  <p className="px-1 py-2 text-sm text-muted-foreground">No products scraped yet.</p>
                ) : (
                  latestProducts.map((p) => (
                    <a
                      key={p.asin}
                      href={p.url ?? undefined}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group flex items-center justify-between gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-accent"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm text-foreground">{p.title ?? p.asin}</p>
                        <p className="text-xs text-muted-foreground">
                          {p.price != null ? `₹${p.price}` : '—'}
                          {p.rating != null && (
                            <span className="ml-2 inline-flex items-center gap-1">
                              <Star className="h-3 w-3 fill-warning text-warning" />
                              {p.rating}
                            </span>
                          )}
                        </p>
                      </div>
                      <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                    </a>
                  ))
                )}
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
        </>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <Card className="mt-4">
      <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/15 text-primary">
          <Sparkles className="h-7 w-7" />
        </div>
        <div>
          <p className="text-base font-medium text-foreground">No data yet</p>
          <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
            Scrape a product, a keyword search, or a batch file to populate your catalog and start asking
            questions about it.
          </p>
        </div>
        <Button asChild>
          <Link to="/scrape">
            <PackageSearch />
            Scrape your first product
          </Link>
        </Button>
      </CardContent>
    </Card>
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
