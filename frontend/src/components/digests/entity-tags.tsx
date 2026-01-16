import { Badge } from '@/components/ui/badge'

interface EntityTagsProps {
  label: string
  entities?: string[]
}

export function EntityTags({ label, entities }: EntityTagsProps) {
  if (!entities || entities.length === 0) return null

  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase text-foreground/40">{label}</p>
      <div className="flex flex-wrap gap-2">
        {entities.map((entity) => (
          <Badge key={entity} variant="outline">
            {entity}
          </Badge>
        ))}
      </div>
    </div>
  )
}
