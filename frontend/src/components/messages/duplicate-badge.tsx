import { Badge } from '@/components/ui/badge'
import { useTranslation } from 'react-i18next'

interface DuplicateBadgeProps {
  isDuplicate?: boolean
  score?: number | null
}

export function DuplicateBadge({ isDuplicate, score }: DuplicateBadgeProps) {
  const { t } = useTranslation()

  if (!isDuplicate) return null

  return (
    <Badge variant="warning">
      {t('messages.duplicate')}
      {typeof score === 'number' ? ` ${score}%` : ''}
    </Badge>
  )
}
