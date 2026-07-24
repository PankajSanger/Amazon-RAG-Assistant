import { Toaster as Sonner, type ToasterProps } from 'sonner'

import { useTheme } from '@/lib/theme'

function Toaster(props: ToasterProps) {
  const { theme } = useTheme()

  return (
    <Sonner
      theme={theme}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            'group toast bg-card! text-foreground! border-border! shadow-lg!',
          description: 'text-muted-foreground!',
          actionButton: 'bg-primary! text-primary-foreground!',
          cancelButton: 'bg-muted! text-muted-foreground!',
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
