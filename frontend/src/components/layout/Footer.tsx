export function Footer() {
  return (
    <footer className="flex shrink-0 items-center justify-between border-t border-sidebar-border bg-sidebar px-4 py-2.5 text-xs text-muted-foreground sm:px-6 lg:px-8">
      <p>&copy; {new Date().getFullYear()} Amazon RAG</p>
      <p className="hidden sm:block">Product & review intelligence, grounded in your own scraped data.</p>
    </footer>
  )
}
