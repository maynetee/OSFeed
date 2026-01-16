import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import type { Collection } from '@/lib/api/client'

interface CollectionCardProps {
  collection: Collection
  onView?: (id: string) => void
  onEdit?: (collection: Collection) => void
  onDelete?: (id: string) => void
}

export function CollectionCard({ collection, onView, onEdit, onDelete }: CollectionCardProps) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 py-6">
        <div>
          <p className="text-sm font-semibold">{collection.name}</p>
          <p className="text-xs text-foreground/60">
            {collection.channel_ids.length} canaux
          </p>
        </div>
        {collection.description ? (
          <p className="text-xs text-foreground/60">{collection.description}</p>
        ) : null}
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => onView?.(collection.id)}>
            Voir feed
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onEdit?.(collection)}>
            Modifier
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onDelete?.(collection.id)}>
            Supprimer
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
