import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  PackageSearch,
  MessagesSquare,
  Sparkles,
  ShoppingBag,
  Table2,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react'

import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/scrape', label: 'Scrape Data', icon: PackageSearch, end: false },
  { to: '/browse', label: 'Browse Data', icon: Table2, end: false },
  { to: '/ask/products', label: 'Ask Products', icon: ShoppingBag, end: false },
  { to: '/ask/reviews', label: 'Ask Reviews', icon: MessagesSquare, end: false },
]

const STORAGE_KEY = 'sidebar-collapsed'

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(STORAGE_KEY) === 'true')

  function toggle() {
    setCollapsed((prev) => {
      const next = !prev
      localStorage.setItem(STORAGE_KEY, String(next))
      return next
    })
  }

  return (
    <aside
      className={cn(
        'relative flex h-screen shrink-0 flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200',
        collapsed ? 'w-16' : 'w-64',
      )}
    >
      <button
        onClick={toggle}
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        className="absolute -right-3 top-7 flex h-6 w-6 items-center justify-center rounded-full border border-sidebar-border bg-sidebar text-muted-foreground transition-colors hover:text-foreground"
      >
        {collapsed ? <ChevronsRight className="h-3 w-3" /> : <ChevronsLeft className="h-3 w-3" />}
      </button>

      <div className={cn('flex items-center gap-2 px-6 py-6', collapsed && 'justify-center px-0')}>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <Sparkles className="h-4 w-4" />
        </div>
        {!collapsed && (
          <div>
            <p className="text-sm font-semibold leading-none text-foreground">Amazon RAG</p>
            <p className="text-xs text-muted-foreground">Product Intelligence</p>
          </div>
        )}
      </div>

      <nav className={cn('flex flex-1 flex-col gap-1', collapsed ? 'px-2' : 'px-3')}>
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                collapsed && 'justify-center px-0',
                isActive
                  ? 'bg-primary/15 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground',
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {!collapsed && label}
          </NavLink>
        ))}
      </nav>

      {!collapsed && (
        <div className="border-t border-sidebar-border px-6 py-4">
          <p className="text-xs text-muted-foreground">Scraping &middot; RAG &middot; Guardrails</p>
        </div>
      )}
    </aside>
  )
}
