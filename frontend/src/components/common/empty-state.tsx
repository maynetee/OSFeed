import { motion } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/cn'

interface EmptyStateProps {
  title: string
  description: string
  icon?: LucideIcon
  actionLabel?: string
  onAction?: () => void
  secondaryActionLabel?: string
  onSecondaryAction?: () => void
  variant?: 'default' | 'info' | 'warning'
}

const variantStyles = {
  default: 'border-border bg-card/50',
  info: 'border-info/30 bg-info/5',
  warning: 'border-warning/30 bg-warning/5',
}

const iconVariantStyles = {
  default: 'bg-primary/10 text-primary',
  info: 'bg-info/10 text-info',
  warning: 'bg-warning/10 text-warning',
}

export function EmptyState({
  title,
  description,
  icon: Icon,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  variant = 'default',
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'flex flex-col items-center justify-center rounded-2xl border p-12 text-center',
        variantStyles[variant],
      )}
    >
      {Icon && (
        <div
          className={cn(
            'mb-6 flex h-16 w-16 items-center justify-center rounded-2xl',
            iconVariantStyles[variant],
          )}
        >
          <Icon className="h-8 w-8" />
        </div>
      )}
      <h3 className="text-xl font-semibold">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-foreground-muted">{description}</p>
      <div className="mt-6 flex items-center gap-3">
        {actionLabel && onAction && <Button onClick={onAction}>{actionLabel}</Button>}
        {secondaryActionLabel && onSecondaryAction && (
          <Button variant="outline" onClick={onSecondaryAction}>
            {secondaryActionLabel}
          </Button>
        )}
      </div>
    </motion.div>
  )
}
