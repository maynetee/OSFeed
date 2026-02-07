import { useEffect, useState } from 'react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'
import { useTranslation } from 'react-i18next'

interface TrendChartProps {
  data: { date: string; count: number }[]
}

function getCssVariable(variable: string): string {
  if (typeof window === 'undefined') return ''
  const value = getComputedStyle(document.documentElement).getPropertyValue(variable).trim()
  return value ? `hsl(${value})` : ''
}

export function TrendChart({ data }: TrendChartProps) {
  const { t } = useTranslation()

  const [colors, setColors] = useState({
    background: getCssVariable('--card'),
    border: getCssVariable('--border'),
    stroke: getCssVariable('--primary'),
    foregroundMuted: getCssVariable('--foreground-muted'),
    cardForeground: getCssVariable('--card-foreground'),
  })

  useEffect(() => {
    const updateColors = () => {
      setColors({
        background: getCssVariable('--card'),
        border: getCssVariable('--border'),
        stroke: getCssVariable('--primary'),
        foregroundMuted: getCssVariable('--foreground-muted'),
        cardForeground: getCssVariable('--card-foreground'),
      })
    }

    // Update colors on mount
    updateColors()

    // Update colors when theme changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          updateColors()
        }
      })
    })

    observer.observe(document.documentElement, { attributes: true })

    return () => observer.disconnect()
  }, [])

  // Generate accessible description
  const minCount = Math.min(...data.map((d) => d.count))
  const maxCount = Math.max(...data.map((d) => d.count))
  const totalPoints = data.length
  const chartLabel = `Message trend chart showing ${totalPoints} data points from ${data[0]?.date || 'N/A'} to ${data[data.length - 1]?.date || 'N/A'}, ranging from ${minCount} to ${maxCount} messages`

  return (
    <>
      <div
        className="h-64 w-full"
        role="img"
        aria-label={chartLabel}
        aria-describedby="trend-chart-data"
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tick={{ fill: colors.foregroundMuted }}
            />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: colors.foregroundMuted }} />
            <Tooltip
              contentStyle={{
                background: colors.background,
                borderRadius: 12,
                borderColor: colors.border,
                color: colors.cardForeground,
              }}
            />
            <Line
              type="monotone"
              dataKey="count"
              stroke={colors.stroke}
              strokeWidth={3}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {/* Visually hidden data table for screen readers */}
      <table id="trend-chart-data" className="sr-only">
        <caption>{t('stats.trendChartTableCaption')}</caption>
        <thead>
          <tr>
            <th scope="col">{t('stats.trendChartDateHeader')}</th>
            <th scope="col">{t('stats.trendChartCountHeader')}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => (
            <tr key={index}>
              <td>{item.date}</td>
              <td>{item.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}
