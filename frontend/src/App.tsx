import { Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/layout/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { ScrapeData } from '@/pages/ScrapeData'
import { AskProducts } from '@/pages/AskProducts'
import { AskReviews } from '@/pages/AskReviews'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="scrape" element={<ScrapeData />} />
        <Route path="ask/products" element={<AskProducts />} />
        <Route path="ask/reviews" element={<AskReviews />} />
      </Route>
    </Routes>
  )
}

export default App
