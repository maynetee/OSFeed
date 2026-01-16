import { Badge } from '@/components/ui/badge'

interface DuplicateBadgeProps {
  isDuplicate?: boolean
}

export function DuplicateBadge({ isDuplicate }: DuplicateBadgeProps) {
  if (!isDuplicate) return null

  return <Badge variant="warning">Duplicata</Badge>
}
