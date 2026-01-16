import { Badge } from '@/components/ui/badge'

interface LanguageBadgeProps {
  code?: string | null
}

export function LanguageBadge({ code }: LanguageBadgeProps) {
  if (!code) return null
  return <Badge variant="muted">{code.toUpperCase()}</Badge>
}
