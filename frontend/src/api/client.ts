import type {
  AskResponse,
  CreateScrapeJobParams,
  ProductSource,
  ReindexResponse,
  ReviewSource,
  ScrapeJobStatusResponse,
  StatsResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

class ApiError extends Error {}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // no JSON body
    }
    throw new ApiError(detail)
  }
  return res.json() as Promise<T>
}

export function getStats() {
  return fetch(`${API_BASE}/stats`).then((res) => handle<StatsResponse>(res))
}

export function askProducts(query: string) {
  return fetch(`${API_BASE}/products/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  }).then((res) => handle<AskResponse<ProductSource>>(res))
}

export function askReviews(query: string) {
  return fetch(`${API_BASE}/reviews/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  }).then((res) => handle<AskResponse<ReviewSource>>(res))
}

export function reindexProducts() {
  return fetch(`${API_BASE}/products/reindex`, { method: 'POST' }).then((res) =>
    handle<ReindexResponse>(res),
  )
}

export function reindexReviews() {
  return fetch(`${API_BASE}/reviews/reindex`, { method: 'POST' }).then((res) =>
    handle<ReindexResponse>(res),
  )
}

export function createScrapeJob(params: CreateScrapeJobParams) {
  const form = new FormData()
  form.append('input_type', params.inputType)
  form.append('scrape_products', String(params.scrapeProducts))
  form.append('scrape_reviews', String(params.scrapeReviews))

  if (params.url) form.append('url', params.url)
  if (params.keyword) form.append('keyword', params.keyword)
  if (params.pages) form.append('pages', String(params.pages))
  if (params.file) form.append('file', params.file)

  return fetch(`${API_BASE}/scrape/jobs`, { method: 'POST', body: form }).then((res) =>
    handle<{ job_id: string }>(res),
  )
}

export function getScrapeJob(jobId: string) {
  return fetch(`${API_BASE}/scrape/jobs/${jobId}`).then((res) => handle<ScrapeJobStatusResponse>(res))
}

export function scrapeJobDownloadUrl(jobId: string) {
  return `${API_BASE}/scrape/jobs/${jobId}/download`
}
