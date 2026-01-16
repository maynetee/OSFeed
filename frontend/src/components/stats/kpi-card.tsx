import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/cn'

interface KpiCardProps {
  label: string
  value: string
  delta: string
  trend?: 'up' | 'down'
}

export function KpiCard({ label, value, delta, trend = 'up' }: KpiCardProps) {
  const isUp = trend === 'up'

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 py-6">
        <div
          className={cn(
            'inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.2em]',
            isUp ? 'text-success' : 'text-danger',
          )}
        >
          {isUp ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
          {delta}
        </div>
        <div>
          <p className="text-3xl font-semibold tracking-tight">{value}</p>
          <p className="text-sm text-foreground/60">{label}</p>
        </div>
      </CardContent>
    </Card>
  )
}
