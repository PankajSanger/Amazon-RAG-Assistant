import { useState } from 'react'
import { toast } from 'sonner'
import { Download, Loader2, PlayCircle } from 'lucide-react'

import { useCreateScrapeJob, useScrapeJobStatus } from '@/api/hooks'
import { scrapeJobDownloadUrl } from '@/api/client'
import type { ScrapeInputType } from '@/api/types'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'

export function ScrapeData() {
  const [inputType, setInputType] = useState<ScrapeInputType>('single')
  const [url, setUrl] = useState('')
  const [keyword, setKeyword] = useState('')
  const [pages, setPages] = useState(1)
  const [file, setFile] = useState<File | null>(null)
  const [scrapeProducts, setScrapeProducts] = useState(true)
  const [scrapeReviews, setScrapeReviews] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)

  const createJob = useCreateScrapeJob()
  const jobStatus = useScrapeJobStatus(jobId)

  const isRunning = jobStatus.data?.status === 'running' || jobStatus.data?.status === 'queued'

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!scrapeProducts && !scrapeReviews) {
      toast.error('Please select at least one scraping option.')
      return
    }

    if (inputType === 'keyword' && !keyword) {
      toast.error('Please enter a keyword.')
      return
    }

    if (inputType === 'single' && !url) {
      toast.error('Please provide a URL.')
      return
    }

    if (inputType === 'file' && !file) {
      toast.error('Please upload an Excel file.')
      return
    }

    createJob.mutate(
      {
        inputType,
        url: inputType === 'single' ? url : undefined,
        keyword: inputType === 'keyword' ? keyword : undefined,
        pages: inputType === 'keyword' ? pages : undefined,
        file: inputType === 'file' ? (file ?? undefined) : undefined,
        scrapeProducts,
        scrapeReviews,
      },
      {
        onSuccess: (data) => setJobId(data.job_id),
        onError: (err) => toast.error(err.message),
      },
    )
  }

  const job = jobStatus.data

  return (
    <div>
      <PageHeader title="Scrape Data" description="Pull product details and customer reviews from Amazon." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[380px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Configure scrape</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
              <div>
                <Label className="mb-3 block">Input type</Label>
                <RadioGroup value={inputType} onValueChange={(v) => setInputType(v as ScrapeInputType)}>
                  <RadioOption value="single" id="single" label="Single URL" />
                  <RadioOption value="file" id="file" label="Upload File" />
                  <RadioOption value="keyword" id="keyword" label="Keyword Search" />
                </RadioGroup>
              </div>

              {inputType === 'single' && (
                <div className="flex flex-col gap-2">
                  <Label htmlFor="url">Amazon product URL</Label>
                  <Input
                    id="url"
                    placeholder="https://www.amazon.in/dp/..."
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                  />
                </div>
              )}

              {inputType === 'file' && (
                <div className="flex flex-col gap-2">
                  <Label htmlFor="file">Excel file (column: url)</Label>
                  <Input
                    id="file"
                    type="file"
                    accept=".xlsx"
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  />
                </div>
              )}

              {inputType === 'keyword' && (
                <>
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="keyword">Keyword</Label>
                    <Input
                      id="keyword"
                      placeholder="hair oil"
                      value={keyword}
                      onChange={(e) => setKeyword(e.target.value)}
                    />
                  </div>
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="pages">Search pages to scrape</Label>
                    <Input
                      id="pages"
                      type="number"
                      min={1}
                      max={50}
                      value={pages}
                      onChange={(e) => setPages(Number(e.target.value))}
                    />
                  </div>
                </>
              )}

              <div>
                <Label className="mb-3 block">Data to scrape</Label>
                <div className="flex flex-col gap-3">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="scrape-products"
                      checked={scrapeProducts}
                      onCheckedChange={(v) => setScrapeProducts(v === true)}
                    />
                    <Label htmlFor="scrape-products" className="font-normal">
                      Product Details
                    </Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="scrape-reviews"
                      checked={scrapeReviews}
                      onCheckedChange={(v) => setScrapeReviews(v === true)}
                    />
                    <Label htmlFor="scrape-reviews" className="font-normal">
                      Customer Reviews
                    </Label>
                  </div>
                </div>
              </div>

              <Button type="submit" disabled={createJob.isPending || isRunning}>
                {createJob.isPending || isRunning ? <Loader2 className="animate-spin" /> : <PlayCircle />}
                Start Scraping
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="flex flex-col gap-6">
          {!job && (
            <Card>
              <CardContent className="flex h-48 items-center justify-center text-sm text-muted-foreground">
                Configure a scrape on the left and click "Start Scraping" to see live progress here.
              </CardContent>
            </Card>
          )}

          {job && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Job status</CardTitle>
                  <StatusBadge status={job.status} />
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <Progress value={job.progress} />
                <p className="text-sm text-muted-foreground">{job.message}</p>
                {job.error && <p className="text-sm text-destructive">{job.error}</p>}

                {job.status === 'done' && (
                  <div className="mt-2 flex items-center gap-4">
                    <span className="text-sm text-foreground">
                      {job.product_count} product(s), {job.review_count} review(s) saved
                    </span>
                    {job.download_ready && (
                      <Button variant="secondary" size="sm" asChild>
                        <a href={scrapeJobDownloadUrl(job.job_id)} download>
                          <Download />
                          Download Excel
                        </a>
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {job?.products_preview && job.products_preview.length > 0 && (
            <PreviewCard title="Product Details" rows={job.products_preview} />
          )}

          {job?.reviews_preview && job.reviews_preview.length > 0 && (
            <PreviewCard title="Customer Reviews" rows={job.reviews_preview} />
          )}
        </div>
      </div>
    </div>
  )
}

function RadioOption({ value, id, label }: { value: string; id: string; label: string }) {
  return (
    <div className="flex items-center gap-2 py-1">
      <RadioGroupItem value={value} id={id} />
      <Label htmlFor={id} className="font-normal">
        {label}
      </Label>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === 'done' ? 'success' : status === 'error' ? 'destructive' : status === 'running' ? 'default' : 'secondary'
  return <Badge variant={variant}>{status}</Badge>
}

function PreviewCard({ title, rows }: { title: string; rows: Record<string, unknown>[] }) {
  const columns = Object.keys(rows[0] ?? {}).filter((c) => c !== 'about' && c !== 'contents')

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title} preview</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col) => (
                <TableHead key={col}>{col}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.slice(0, 10).map((row, i) => (
              <TableRow key={i}>
                {columns.map((col) => (
                  <TableCell key={col} className="max-w-56 truncate">
                    {String(row[col] ?? '—')}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
