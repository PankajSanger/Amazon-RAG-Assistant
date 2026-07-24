import { Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/layout/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { ScrapeData } from '@/pages/ScrapeData'
import { AskProducts } from '@/pages/AskProducts'
import { AskReviews } from '@/pages/AskReviews'
import { BrowseData } from '@/pages/BrowseData'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="scrape" element={<ScrapeData />} />
        <Route path="browse" element={<BrowseData />} />
        <Route path="ask/products" element={<AskProducts />} />
        <Route path="ask/reviews" element={<AskReviews />} />
      </Route>
    </Routes>
  )
}

export default App
