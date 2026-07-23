import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const ACCENT = '#6366f1'

export function RatingChart({ distribution }: { distribution: Record<string, number> }) {
  const data = Object.entries(distribution)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([stars, count]) => ({ stars: `${stars}★`, count }))

  const isEmpty = data.every((d) => d.count === 0)

  return (
    <div className="h-56 w-full">
      {isEmpty ? (
        <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No product ratings yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="#1e2536" strokeDasharray="0" />
            <XAxis
              dataKey="stars"
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#8b93a7', fontSize: 12 }}
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#8b93a7', fontSize: 12 }}
              width={36}
            />
            <Tooltip
              cursor={{ fill: 'rgba(99,102,241,0.08)' }}
              contentStyle={{
                background: '#0d1220',
                border: '1px solid #1e2536',
                borderRadius: 8,
                fontSize: 12,
                color: '#f1f5f9',
              }}
              labelStyle={{ color: '#8b93a7' }}
            />
            <Bar dataKey="count" name="Products" fill={ACCENT} radius={[4, 4, 0, 0]} maxBarSize={40} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
