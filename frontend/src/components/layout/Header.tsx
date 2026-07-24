import { useLocation } from 'react-router-dom'
import { Menu, Sparkles } from 'lucide-react'

import { NAV_ITEMS } from './Sidebar'
import { ThemeToggle } from '@/components/ThemeToggle'

export function Header({ onOpenMobileMenu }: { onOpenMobileMenu: () => void }) {
  const location = useLocation()
  const current = NAV_ITEMS.find((item) => (item.end ? location.pathname === item.to : location.pathname.startsWith(item.to)))

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-sidebar-border bg-sidebar px-4 sm:px-6 lg:px-8">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileMenu}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground md:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2 md:hidden">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/15 text-primary">
            <Sparkles className="h-3.5 w-3.5" />
          </div>
          <p className="text-sm font-semibold leading-none text-foreground">Amazon RAG</p>
        </div>
        <p className="hidden text-sm font-medium text-muted-foreground md:block">{current?.label ?? ''}</p>
      </div>

      <ThemeToggle />
    </header>
  )
}
