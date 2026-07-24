import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { Footer } from './Footer'

export function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header onOpenMobileMenu={() => setMobileOpen(true)} />

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto flex h-full max-w-6xl flex-col px-4 py-6 sm:px-6 sm:py-10 lg:px-8">
            <Outlet />
          </div>
        </main>

        <Footer />
      </div>
    </div>
  )
}
