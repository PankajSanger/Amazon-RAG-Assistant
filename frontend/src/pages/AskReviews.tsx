import { useAskReviews, useReindexReviews } from '@/api/hooks'
import { AskExperience } from '@/components/AskExperience'
import { ReviewSourceCard } from '@/components/SourceCard'

const SUGGESTIONS = [
  'What do customers say about the smell of the hair oil?',
  'Are there any complaints about leakage or packaging?',
  'What do people like most?',
]

export function AskReviews() {
  return (
    <AskExperience
      title="Ask About Reviews"
      description="Query scraped customer reviews for complaints, praise and usage feedback."
      placeholder="Ask a question about the scraped reviews..."
      suggestions={SUGGESTIONS}
      storageKey="ask-reviews-history"
      useAsk={useAskReviews}
      useReindex={useReindexReviews}
      renderSource={(source, key) => <ReviewSourceCard key={key} source={source} />}
    />
  )
}
