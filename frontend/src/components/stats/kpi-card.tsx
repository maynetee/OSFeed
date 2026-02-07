import { ArrowUpRight, ArrowDownRight, type LucideIcon } from 'lucide-react'
import { motion } from 'framer-motion'

import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/cn'

interface KpiCardProps {
  label: string
  value: string
  delta?: string
  trend?: 'up' | 'down'
  icon?: LucideIcon
  accentColor?: string
}

export function KpiCard({
  label,
  value,
  delta,
  trend = 'up',
  icon: Icon,
  accentColor = 'primary',
}: KpiCardProps) {
  const isUp = trend === 'up'

  const colorMap: Record<string, { bg: string; text: string }> = {
    primary: { bg: 'bg-primary/10', text: 'text-primary' },
    amber: { bg: 'bg-amber-500/10', text: 'text-amber-500' },
    emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-500' },
    blue: { bg: 'bg-blue-500/10', text: 'text-blue-500' },
  }

  const colors = colorMap[accentColor] ?? colorMap.primary

  return (
    <motion.div
      whileHover={{ y: -4, boxShadow: '0 8px 30px rgba(0,0,0,0.12)' }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
    >
      <Card className="overflow-hidden">
        <CardContent className="flex items-start gap-4 py-6">
          {Icon && (
            <div
              className={cn(
                'flex h-11 w-11 shrink-0 items-center justify-center rounded-full',
                colors.bg,
              )}
            >
              <Icon className={cn('h-5 w-5', colors.text)} />
            </div>
          )}
          <div className="flex flex-col gap-1 min-w-0">
            {delta ? (
              <div
                className={cn(
                  'inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-[0.2em]',
                  isUp ? 'text-success' : 'text-danger',
                )}
              >
                {isUp ? (
                  <ArrowUpRight className="h-3.5 w-3.5" />
                ) : (
                  <ArrowDownRight className="h-3.5 w-3.5" />
                )}
                {delta}
              </div>
            ) : null}
            <p className="text-3xl font-semibold tracking-tight">{value}</p>
            <p className="text-sm text-foreground/60">{label}</p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
