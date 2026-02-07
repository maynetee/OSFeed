import { useTranslation } from 'react-i18next'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
} from 'recharts'

interface EscalationTrendData {
  date: string
  high_count: number
  medium_count: number
  low_count: number
}

interface EscalationChartProps {
  data: EscalationTrendData[]
}

export default function EscalationChart({ data }: EscalationChartProps) {
  const { t } = useTranslation()

  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
          <XAxis dataKey="date" tickLine={false} axisLine={false} className="text-xs" />
          <YAxis tickLine={false} axisLine={false} className="text-xs" />
          <RechartsTooltip />
          <Area
            type="monotone"
            dataKey="high_count"
            stackId="1"
            stroke="#ef4444"
            fill="#ef4444"
            fillOpacity={0.3}
            name={t('analysis.escalation.high')}
          />
          <Area
            type="monotone"
            dataKey="medium_count"
            stackId="1"
            stroke="#f59e0b"
            fill="#f59e0b"
            fillOpacity={0.3}
            name={t('analysis.escalation.medium')}
          />
          <Area
            type="monotone"
            dataKey="low_count"
            stackId="1"
            stroke="#22c55e"
            fill="#22c55e"
            fillOpacity={0.1}
            name={t('analysis.escalation.low')}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
