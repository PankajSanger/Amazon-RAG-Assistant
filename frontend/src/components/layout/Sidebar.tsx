import { NavLink } from 'react-router-dom'
import { LayoutDashboard, PackageSearch, MessagesSquare, Sparkles, ShoppingBag, Table2 } from 'lucide-react'

import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/scrape', label: 'Scrape Data', icon: PackageSearch, end: false },
  { to: '/browse', label: 'Browse Data', icon: Table2, end: false },
  { to: '/ask/products', label: 'Ask Products', icon: ShoppingBag, end: false },
  { to: '/ask/reviews', label: 'Ask Reviews', icon: MessagesSquare, end: false },
]

export function Sidebar() {
  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar">
      <div className="flex items-center gap-2 px-6 py-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold leading-none text-foreground">Amazon RAG</p>
          <p className="text-xs text-muted-foreground">Product Intelligence</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/15 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground',
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-sidebar-border px-6 py-4">
        <p className="text-xs text-muted-foreground">Scraping &middot; RAG &middot; Guardrails</p>
      </div>
    </aside>
  )
}
