import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { useTheme } from '@/lib/theme'

const ACCENT = '#6366f1'

const PALETTE = {
  dark: { grid: '#1e2536', tick: '#8b93a7', tooltipBg: '#0d1220', tooltipBorder: '#1e2536', tooltipText: '#f1f5f9' },
  light: { grid: '#e2e8f0', tick: '#64748b', tooltipBg: '#ffffff', tooltipBorder: '#e2e8f0', tooltipText: '#0f172a' },
}

export function RatingChart({ distribution }: { distribution: Record<string, number> }) {
  const { theme } = useTheme()
  const colors = PALETTE[theme]

  const data = Object.entries(distribution)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([stars, count]) => ({ stars: `${stars}★`, count }))

  const isEmpty = data.every((d) => d.count === 0)

  return (
    <div className="h-56 w-full">
      {isEmpty ? (
        <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No ratings yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke={colors.grid} strokeDasharray="0" />
            <XAxis
              dataKey="stars"
              tickLine={false}
              axisLine={false}
              tick={{ fill: colors.tick, fontSize: 12 }}
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              tick={{ fill: colors.tick, fontSize: 12 }}
              width={36}
            />
            <Tooltip
              cursor={{ fill: 'rgba(99,102,241,0.08)' }}
              contentStyle={{
                background: colors.tooltipBg,
                border: `1px solid ${colors.tooltipBorder}`,
                borderRadius: 8,
                fontSize: 12,
                color: colors.tooltipText,
              }}
              labelStyle={{ color: colors.tick }}
            />
            <Bar dataKey="count" name="Count" fill={ACCENT} radius={[4, 4, 0, 0]} maxBarSize={40} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
