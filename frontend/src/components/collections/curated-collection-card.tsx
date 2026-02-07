import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation } from '@tanstack/react-query'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ConfirmDialog } from '@/components/common/confirm-dialog'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { curatedCollectionsApi, type CuratedCollection } from '@/lib/api/client'

const regionColors: Record<string, string> = {
  Europe: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  'Middle East': 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  'Asia-Pacific': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  Americas: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  Africa: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  Global: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
}

interface CuratedCollectionCardProps {
  collection: CuratedCollection
}

export function CuratedCollectionCard({ collection }: CuratedCollectionCardProps) {
  const { t } = useTranslation()
  const [detailOpen, setDetailOpen] = useState(false)
  const [importResult, setImportResult] = useState<{
    imported_count: number
    already_existed: number
  } | null>(null)

  const importMutation = useMutation({
    mutationFn: () => curatedCollectionsApi.import(collection.id),
    onSuccess: (res) => {
      setImportResult(res.data)
    },
  })

  return (
    <Card className="animate-rise-in flex flex-col">
      <CardContent className="flex flex-1 flex-col gap-3 py-6">
        <div>
          <p className="text-sm font-semibold">{collection.name}</p>
          {collection.description && (
            <p className="mt-1 line-clamp-2 text-xs text-foreground/60">{collection.description}</p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="muted">
            {t('curatedCollections.channelCount', { count: collection.channel_count })}
          </Badge>
          {collection.region && (
            <Badge className={regionColors[collection.region] ?? 'bg-muted text-foreground/60'}>
              {collection.region}
            </Badge>
          )}
          {collection.topic && <Badge variant="outline">{collection.topic}</Badge>}
        </div>

        {collection.curator && (
          <p className="text-xs text-foreground/40">
            {t('curatedCollections.curatedBy', { curator: collection.curator })}
          </p>
        )}

        <div className="mt-auto flex flex-wrap items-center gap-2 pt-2">
          <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="sm">
                {t('curatedCollections.viewDetails')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{collection.name}</DialogTitle>
                {collection.description && (
                  <DialogDescription>{collection.description}</DialogDescription>
                )}
              </DialogHeader>

              <div className="mt-4 space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  {collection.region && (
                    <Badge
                      className={regionColors[collection.region] ?? 'bg-muted text-foreground/60'}
                    >
                      {collection.region}
                    </Badge>
                  )}
                  {collection.topic && <Badge variant="outline">{collection.topic}</Badge>}
                  <Badge variant="muted">
                    {t('curatedCollections.channelCount', { count: collection.channel_count })}
                  </Badge>
                </div>

                {collection.curator && (
                  <p className="text-sm text-foreground/60">
                    {t('curatedCollections.curatedBy', { curator: collection.curator })}
                  </p>
                )}

                {collection.last_curated_at && (
                  <p className="text-xs text-foreground/40">
                    {t('curatedCollections.lastUpdated')}:{' '}
                    {new Date(collection.last_curated_at).toLocaleDateString()}
                  </p>
                )}

                <div>
                  <p className="mb-2 text-sm font-medium">{t('curatedCollections.channels')}</p>
                  <div className="max-h-48 overflow-y-auto rounded-lg border border-border p-3">
                    {collection.curated_channel_usernames.length > 0 ? (
                      <ul className="space-y-1">
                        {collection.curated_channel_usernames.map((username) => (
                          <li key={username} className="text-xs text-foreground/70">
                            @{username}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-foreground/40">-</p>
                    )}
                  </div>
                </div>

                {importResult ? (
                  <div className="rounded-lg border border-success/30 bg-success/5 p-3">
                    <p className="text-sm text-success">
                      {t('curatedCollections.importSuccess', {
                        count: importResult.imported_count,
                        existed: importResult.already_existed,
                      })}
                    </p>
                  </div>
                ) : (
                  <ConfirmDialog
                    title={t('curatedCollections.importAll')}
                    description={t('curatedCollections.importConfirm', {
                      count: collection.channel_count,
                    })}
                    confirmText={t('curatedCollections.importAll')}
                    onConfirm={async () => {
                      await importMutation.mutateAsync()
                    }}
                    triggerButton={
                      <Button disabled={importMutation.isPending}>
                        {t('curatedCollections.importAll')}
                      </Button>
                    }
                  />
                )}
              </div>
            </DialogContent>
          </Dialog>

          <ConfirmDialog
            title={t('curatedCollections.importAll')}
            description={t('curatedCollections.importConfirm', { count: collection.channel_count })}
            confirmText={t('curatedCollections.importAll')}
            onConfirm={async () => {
              await importMutation.mutateAsync()
            }}
            triggerButton={
              <Button size="sm" disabled={importMutation.isPending || !!importResult}>
                {t('curatedCollections.importAll')}
              </Button>
            }
          />
        </div>
      </CardContent>
    </Card>
  )
}
