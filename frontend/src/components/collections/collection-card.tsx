import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import type { Collection } from '@/lib/api/client'
import { useTranslation } from 'react-i18next'

interface CollectionCardProps {
  collection: Collection
  onView?: (id: string) => void
  onEdit?: (collection: Collection) => void
  onDelete?: (id: string) => void
}

export function CollectionCard({ collection, onView, onEdit, onDelete }: CollectionCardProps) {
  const { t } = useTranslation()

  return (
    <Card className="animate-rise-in">
      <CardContent className="flex flex-col gap-4 py-6">
        <div>
          <p className="text-sm font-semibold">{collection.name}</p>
          <p className="text-xs text-foreground/60">
            {t('collections.channelsCount', { count: collection.channel_ids.length })}
          </p>
        </div>
        {collection.description ? (
          <p className="text-xs text-foreground/60">{collection.description}</p>
        ) : null}
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="lg" onClick={() => onView?.(collection.id)}>
            {t('collections.viewFeed')}
          </Button>
          <Button variant="ghost" size="lg" onClick={() => onEdit?.(collection)}>
            {t('collections.edit')}
          </Button>
          <Button variant="ghost" size="lg" onClick={() => onDelete?.(collection.id)}>
            {t('collections.delete')}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
