import { useEffect, useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, ExternalLink, Search, Star } from 'lucide-react'

import { useProducts, useReviews } from '@/api/hooks'
import type { Product, Review } from '@/api/types'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 10

type SortDirection = 'asc' | 'desc'

function SortableHeader<T extends string>({
  column,
  label,
  activeColumn,
  direction,
  onSort,
  className,
}: {
  column: T
  label: string
  activeColumn: T
  direction: SortDirection
  onSort: (column: T) => void
  className?: string
}) {
  const isActive = column === activeColumn
  const Icon = isActive ? (direction === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown

  return (
    <TableHead className={className}>
      <button
        onClick={() => onSort(column)}
        className={cn(
          'flex items-center gap-1 transition-colors hover:text-foreground',
          isActive && 'text-foreground',
        )}
      >
        {label}
        <Icon className="h-3 w-3" />
      </button>
    </TableHead>
  )
}

function useSorted<T, K extends string>(
  rows: T[],
  sortColumn: K,
  sortDirection: SortDirection,
  getSortValue: (row: T, column: K) => string | number | null,
) {
  return useMemo(() => {
    return [...rows].sort((a, b) => {
      const va = getSortValue(a, sortColumn)
      const vb = getSortValue(b, sortColumn)
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      const cmp = typeof va === 'string' ? va.localeCompare(vb as string) : va - (vb as number)
      return sortDirection === 'asc' ? cmp : -cmp
    })
  }, [rows, sortColumn, sortDirection, getSortValue])
}

type ProductColumn = 'title' | 'price' | 'rating' | 'no_of_ratings'
type ReviewColumn = 'author' | 'rating' | 'date' | 'asin'

function Pagination({
  page,
  totalPages,
  onChange,
}: {
  page: number
  totalPages: number
  onChange: (page: number) => void
}) {
  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-end gap-3">
      <p className="text-xs text-muted-foreground">
        Page {page} of {totalPages}
      </p>
      <div className="flex items-center gap-1">
        <Button variant="outline" size="icon" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          <ChevronLeft />
        </Button>
        <Button variant="outline" size="icon" disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
          <ChevronRight />
        </Button>
      </div>
    </div>
  )
}

export function BrowseData() {
  return (
    <div>
      <PageHeader title="Browse Data" description="Search and sort the full scraped catalog." />
      <Tabs defaultValue="products">
        <TabsList>
          <TabsTrigger value="products">Products</TabsTrigger>
          <TabsTrigger value="reviews">Reviews</TabsTrigger>
        </TabsList>
        <TabsContent value="products">
          <ProductsTable />
        </TabsContent>
        <TabsContent value="reviews">
          <ReviewsTable />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function ProductsTable() {
  const { data, isLoading } = useProducts()
  const [search, setSearch] = useState('')
  const [sortColumn, setSortColumn] = useState<ProductColumn>('no_of_ratings')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [page, setPage] = useState(1)

  function handleSort(column: ProductColumn) {
    if (column === sortColumn) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortColumn(column)
      setSortDirection('desc')
    }
  }

  const filtered = useMemo(() => {
    if (!data) return []
    const q = search.trim().toLowerCase()
    if (!q) return data
    return data.filter((p) => p.title?.toLowerCase().includes(q) || p.asin.toLowerCase().includes(q))
  }, [data, search])

  const sorted = useSorted(filtered, sortColumn, sortDirection, (p: Product, col) => p[col])

  useEffect(() => setPage(1), [search, sortColumn, sortDirection])

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE))
  const pageItems = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  if (isLoading) return <Skeleton className="mt-4 h-64" />

  return (
    <div className="mt-4 flex flex-col gap-3">
      <SearchBar value={search} onChange={setSearch} placeholder="Search products by title or ASIN..." />
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {sorted.length} of {data?.length ?? 0} products
        </p>
        <Pagination page={page} totalPages={totalPages} onChange={setPage} />
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <SortableHeader column="title" label="Title" activeColumn={sortColumn} direction={sortDirection} onSort={handleSort} />
            <SortableHeader column="price" label="Price" activeColumn={sortColumn} direction={sortDirection} onSort={handleSort} />
            <SortableHeader column="rating" label="Rating" activeColumn={sortColumn} direction={sortDirection} onSort={handleSort} />
            <SortableHeader column="no_of_ratings" label="Ratings" activeColumn={sortColumn} direction={sortDirection} onSort={handleSort} />
            <TableHead>Link</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {pageItems.map((p) => (
            <TableRow key={p.asin}>
              <TableCell className="max-w-md">
                <span className="line-clamp-2">{p.title ?? '—'}</span>
              </TableCell>
              <TableCell>{p.price != null ? `₹${p.price}` : '—'}</TableCell>
              <TableCell>
                {p.rating != null ? (
                  <span className="flex items-center gap-1">
                    <Star className="h-3 w-3 fill-warning text-warning" />
                    {p.rating}
                  </span>
                ) : (
                  '—'
                )}
              </TableCell>
              <TableCell>{p.no_of_ratings ?? '—'}</TableCell>
              <TableCell>
                {p.url && (
                  <a
                    href={p.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-primary hover:underline"
                  >
                    View <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

function ReviewsTable() {
  const { data, isLoading } = useReviews()
  const [search, setSearch] = useState('')
  const [sortColumn, setSortColumn] = useState<ReviewColumn>('date')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [page, setPage] = useState(1)

  function handleSort(column: ReviewColumn) {
    if (column === sortColumn) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortColumn(column)
      setSortDirection('desc')
    }
  }

  const filtered = useMemo(() => {
    if (!data) return []
    const q = search.trim().toLowerCase()
    if (!q) return data
    return data.filter(
      (r) => r.author?.toLowerCase().includes(q) || r.contents?.toLowerCase().includes(q) || r.asin?.toLowerCase().includes(q),
    )
  }, [data, search])

  const sorted = useSorted(filtered, sortColumn, sortDirection, (r: Review, col) => r[col])

  useEffect(() => setPage(1), [search, sortColumn, sortDirection])

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE))
  const pageItems = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  if (isLoading) return <Skeleton className="mt-4 h-64" />

  return (
    <div className="mt-4 flex flex-col gap-3">
      <SearchBar value={search} onChange={setSearch} placeholder="Search reviews by author, content, or ASIN..." />
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {sorted.length} of {data?.length ?? 0} reviews
        </p>
        <Pagination page={page} totalPages={totalPages} onChange={setPage} />
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <SortableHeader column="author" label="Author" activeColumn={sortColumn} direction={sortDirection} onSort={handleSort} />
            <SortableHeader column="rating" label="Rating" activeColumn={sortColumn} direction={sortDirection} onSort={handleSort} />
            <SortableHeader column="date" label="Date" activeColumn={sortColumn} direction={sortDirection} onSort={handleSort} />
            <SortableHeader column="asin" label="ASIN" activeColumn={sortColumn} direction={sortDirection} onSort={handleSort} />
            <TableHead>Review</TableHead>
            <TableHead>Link</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {pageItems.map((r) => (
            <TableRow key={r.url}>
              <TableCell>{r.author ?? 'Amazon Customer'}</TableCell>
              <TableCell>
                {r.rating != null ? (
                  <span className="flex items-center gap-1">
                    <Star className="h-3 w-3 fill-warning text-warning" />
                    {r.rating}
                  </span>
                ) : (
                  '—'
                )}
              </TableCell>
              <TableCell>{r.date ?? '—'}</TableCell>
              <TableCell>{r.asin ?? '—'}</TableCell>
              <TableCell className="max-w-md">
                <span className="line-clamp-2">{r.contents ?? '—'}</span>
              </TableCell>
              <TableCell>
                {r.url && (
                  <a
                    href={r.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-primary hover:underline"
                  >
                    View <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

function SearchBar({
  value,
  onChange,
  placeholder,
}: {
  value: string
  onChange: (v: string) => void
  placeholder: string
}) {
  return (
    <div className="relative max-w-md">
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="pl-9" />
    </div>
  )
}
