import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Menu, Sparkles } from 'lucide-react'

import { Sidebar } from './Sidebar'

export function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-sidebar-border bg-sidebar px-4 py-3 md:hidden">
          <button
            onClick={() => setMobileOpen(true)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/15 text-primary">
              <Sparkles className="h-3.5 w-3.5" />
            </div>
            <p className="text-sm font-semibold leading-none text-foreground">Amazon RAG</p>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
