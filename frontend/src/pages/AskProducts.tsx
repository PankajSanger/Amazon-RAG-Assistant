import { useAskProducts, useReindexProducts } from '@/api/hooks'
import { AskExperience } from '@/components/AskExperience'
import { ProductSourceCard } from '@/components/SourceCard'

const SUGGESTIONS = [
  'Which hair oil is best for hair fall control?',
  'Suggest a hair oil under 500 rupees with a good rating.',
  'Compare the top rated products',
]

export function AskProducts() {
  return (
    <AskExperience
      title="Ask About Products"
      description="Query scraped product titles, prices, ratings and descriptions."
      placeholder="Ask a question about the scraped products..."
      suggestions={SUGGESTIONS}
      useAsk={useAskProducts}
      useReindex={useReindexProducts}
      renderSource={(source, key) => <ProductSourceCard key={key} source={source} />}
    />
  )
}
