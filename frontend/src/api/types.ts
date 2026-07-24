export interface StatsResponse {
  product_count: number
  review_count: number
  avg_product_rating: number | null
  avg_review_rating: number | null
  rating_distribution: Record<string, number>
}

export interface ProductSource {
  asin?: string | null
  title?: string | null
  rating?: number | null
  no_of_ratings?: number | null
  price?: number | null
  url?: string | null
}

export interface ReviewSource {
  asin?: string | null
  author?: string | null
  rating?: number | null
  date?: string | null
  url?: string | null
}

export interface Product {
  asin: string
  title: string | null
  rating: number | null
  no_of_ratings: number | null
  price: number | null
  about: string | null
  url: string | null
}

export interface Review {
  url: string
  asin: string | null
  author: string | null
  rating: number | null
  date: string | null
  title: string | null
  contents: string | null
}

export interface AskResponse<TSource = Record<string, unknown>> {
  answer: string
  sources: TSource[]
}

export interface ReindexResponse {
  indexed_count: number
}

export type JobStatus = 'queued' | 'running' | 'done' | 'error'

export interface ScrapeJobStatusResponse {
  job_id: string
  status: JobStatus
  progress: number
  message: string
  product_count: number
  review_count: number
  products_preview: Record<string, unknown>[]
  reviews_preview: Record<string, unknown>[]
  error: string | null
  download_ready: boolean
}

export type ScrapeInputType = 'single' | 'file' | 'keyword'

export interface CreateScrapeJobParams {
  inputType: ScrapeInputType
  url?: string
  keyword?: string
  pages?: number
  scrapeProducts: boolean
  scrapeReviews: boolean
  file?: File
}
