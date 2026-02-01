import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { Collection } from '@/lib/api/client'
import { collectionsApi } from '@/lib/api/client'

interface ChannelCollectionPickerProps {
  channelId: string
  collections: Collection[]
}

export function ChannelCollectionPicker({ channelId, collections }: ChannelCollectionPickerProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [newCollectionName, setNewCollectionName] = useState('')

  useEffect(() => {
    if (open) {
      const initial = collections
        .filter((collection) => collection.channel_ids.includes(channelId))
        .map((collection) => collection.id)
      setSelectedIds(initial)
    }
  }, [open, collections, channelId])

  const updateCollections = useMutation({
    mutationFn: async () => {
      const updates = collections.map((collection) => {
        const hasChannel = collection.channel_ids.includes(channelId)
        const shouldHave = selectedIds.includes(collection.id)
        if (hasChannel === shouldHave) {
          return Promise.resolve(null)
        }
        const nextChannelIds = shouldHave
          ? [...collection.channel_ids, channelId]
          : collection.channel_ids.filter((id) => id !== channelId)
        return collectionsApi.update(collection.id, { channel_ids: nextChannelIds })
      })
      await Promise.all(updates)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['collections'] })
      setOpen(false)
    },
  })

  const createCollection = useMutation({
    mutationFn: async () => {
      if (!newCollectionName.trim()) return
      const response = await collectionsApi.create({ name: newCollectionName.trim() })
      setSelectedIds((prev) => [...prev, response.data.id])
      setNewCollectionName('')
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections'] }),
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          {t('channels.assignCollections')}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('channels.assignCollectionsTitle')}</DialogTitle>
        </DialogHeader>
        <div className="mt-4 flex flex-col gap-3">
          <div className="flex flex-col gap-2">
            <Label className="text-xs font-semibold uppercase text-foreground/40">
              {t('collections.create')}
            </Label>
            <div className="flex gap-2">
              <Input
                value={newCollectionName}
                onChange={(event) => setNewCollectionName(event.target.value)}
                placeholder={t('collections.namePlaceholder')}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => createCollection.mutate()}
                disabled={!newCollectionName.trim()}
              >
                {t('collections.save')}
              </Button>
            </div>
          </div>
          <fieldset className="flex flex-col gap-2">
            <legend className="text-xs font-semibold uppercase text-foreground/40">
              {t('collections.title')}
            </legend>
            <div className="flex flex-wrap gap-2">
              {collections.map((collection) => {
                const active = selectedIds.includes(collection.id)
                return (
                  <Button
                    key={collection.id}
                    variant={active ? 'secondary' : 'outline'}
                    size="sm"
                    aria-pressed={active}
                    onClick={() =>
                      setSelectedIds(
                        active
                          ? selectedIds.filter((id) => id !== collection.id)
                          : [...selectedIds, collection.id],
                      )
                    }
                  >
                    {collection.name}
                  </Button>
                )
              })}
            </div>
          </fieldset>
          <Button onClick={() => updateCollections.mutate()} disabled={updateCollections.isPending}>
            {updateCollections.isPending ? t('collections.saving') : t('collections.save')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
