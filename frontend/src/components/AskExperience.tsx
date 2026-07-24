import { type FormEvent, type ReactNode, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Loader2, RefreshCw, Send, Sparkles, Trash2 } from 'lucide-react'
import type { UseMutationResult } from '@tanstack/react-query'

import type { AskResponse, ReindexResponse } from '@/api/types'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

interface Exchange<TSource> {
  id: string
  query: string
  answer?: string
  sources?: TSource[]
  status: 'pending' | 'done' | 'error'
  error?: string
}

function loadHistory<TSource>(storageKey: string): Exchange<TSource>[] {
  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) return []
    const parsed = JSON.parse(raw) as Exchange<TSource>[]
    // Drop anything that was still "pending" when the page closed - there's
    // no in-flight request to resolve it anymore.
    return parsed.filter((ex) => ex.status !== 'pending')
  } catch {
    return []
  }
}

export function AskExperience<TSource>({
  title,
  description,
  placeholder,
  suggestions,
  storageKey,
  useAsk,
  useReindex,
  renderSource,
}: {
  title: string
  description: string
  placeholder: string
  suggestions: string[]
  storageKey: string
  useAsk: () => UseMutationResult<AskResponse<TSource>, Error, string>
  useReindex: () => UseMutationResult<ReindexResponse, Error, void>
  renderSource: (source: TSource, key: number) => ReactNode
}) {
  const [query, setQuery] = useState('')
  const [exchanges, setExchanges] = useState<Exchange<TSource>[]>(() => loadHistory<TSource>(storageKey))

  const ask = useAsk()
  const reindex = useReindex()

  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(exchanges))
  }, [storageKey, exchanges])

  function clearHistory() {
    setExchanges([])
    localStorage.removeItem(storageKey)
  }

  function submit(question: string) {
    const trimmed = question.trim()
    if (!trimmed || ask.isPending) return

    const id = crypto.randomUUID()
    setExchanges((prev) => [...prev, { id, query: trimmed, status: 'pending' }])
    setQuery('')

    ask.mutate(trimmed, {
      onSuccess: (data) => {
        setExchanges((prev) =>
          prev.map((ex) => (ex.id === id ? { ...ex, status: 'done', answer: data.answer, sources: data.sources } : ex)),
        )
      },
      onError: (err) => {
        setExchanges((prev) =>
          prev.map((ex) => (ex.id === id ? { ...ex, status: 'error', error: err.message } : ex)),
        )
      },
    })
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    submit(query)
  }

  function handleReindex() {
    reindex.mutate(undefined, {
      onSuccess: (data) => toast.success(`Indexed ${data.indexed_count} item(s).`),
      onError: (err) => toast.error(err.message),
    })
  }

  return (
    <div className="flex h-[calc(100vh-5rem)] flex-col">
      <PageHeader
        title={title}
        description={description}
        action={
          <div className="flex items-center gap-2">
            {exchanges.length > 0 && (
              <Button variant="ghost" onClick={clearHistory} title="Clear conversation">
                <Trash2 />
                Clear
              </Button>
            )}
            <Button variant="secondary" onClick={handleReindex} disabled={reindex.isPending}>
              {reindex.isPending ? <Loader2 className="animate-spin" /> : <RefreshCw />}
              Rebuild Index
            </Button>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto pr-1">
        {exchanges.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/15 text-primary">
              <Sparkles className="h-6 w-6" />
            </div>
            <p className="max-w-sm text-sm text-muted-foreground">
              Ask a question in plain English. Answers are grounded only in your scraped data.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => submit(s)}
                  className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-6 pb-4">
            {exchanges.map((exchange) => (
              <div key={exchange.id} className="flex flex-col gap-3">
                <div className="ml-auto max-w-xl rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                  {exchange.query}
                </div>

                <Card className={cn('max-w-2xl', exchange.status === 'error' && 'border-destructive/40')}>
                  <CardContent className="p-4">
                    {exchange.status === 'pending' && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Thinking...
                      </div>
                    )}

                    {exchange.status === 'error' && (
                      <p className="text-sm text-destructive">{exchange.error}</p>
                    )}

                    {exchange.status === 'done' && (
                      <>
                        <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                          {exchange.answer}
                        </p>
                        {exchange.sources && exchange.sources.length > 0 && (
                          <div className="mt-4 flex flex-col gap-2 border-t border-border pt-3">
                            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                              Sources ({exchange.sources.length})
                            </p>
                            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                              {exchange.sources.map((s, i) => renderSource(s, i))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="mt-4 flex items-end gap-2 border-t border-border pt-4">
        <Textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="min-h-11 flex-1 resize-none"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              submit(query)
            }
          }}
        />
        <Button type="submit" disabled={ask.isPending || !query.trim()}>
          {ask.isPending ? <Loader2 className="animate-spin" /> : <Send />}
          Ask
        </Button>
      </form>
    </div>
  )
}
