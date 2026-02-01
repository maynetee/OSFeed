import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
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
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)

  const handleDelete = () => {
    onDelete?.(collection.id)
    setDeleteDialogOpen(false)
  }

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
          <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="lg">
                {t('collections.delete')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('collections.deleteConfirmTitle')}</DialogTitle>
                <DialogDescription>{t('collections.deleteConfirmMessage')}</DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                  {t('common.cancel')}
                </Button>
                <Button variant="destructive" onClick={handleDelete}>
                  {t('collections.delete')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardContent>
    </Card>
  )
}
