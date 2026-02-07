import { memo } from 'react'
import { Badge } from '@/components/ui/badge'
import { useTranslation } from 'react-i18next'

interface DuplicateBadgeProps {
  isDuplicate?: boolean
  score?: number | null
  duplicateCount?: number | null
  onClick?: () => void
}

export const DuplicateBadge = memo(function DuplicateBadge({
  isDuplicate,
  score,
  duplicateCount,
  onClick,
}: DuplicateBadgeProps) {
  const { t } = useTranslation()

  // Show source count badge if we have duplicate_count > 1
  if (duplicateCount && duplicateCount > 1) {
    const variant = duplicateCount <= 3 ? 'warning' : 'danger'
    return (
      <Badge
        variant={variant}
        className={onClick ? 'cursor-pointer hover:opacity-80' : ''}
        onClick={onClick}
      >
        {t('messages.sources', { count: duplicateCount })}
      </Badge>
    )
  }

  // Fallback to original duplicate badge
  if (!isDuplicate) return null

  return (
    <Badge variant="warning">
      {t('messages.duplicate')}
      {typeof score === 'number' ? ` ${score}%` : ''}
    </Badge>
  )
})
