import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { PageTransition } from '@/components/layout/page-transition'
import { CollectionCard } from '@/components/collections/collection-card'
import { CollectionManager } from '@/components/collections/collection-manager'
import { EmptyState } from '@/components/common/empty-state'
import { Layers } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { collectionsApi, type Collection } from '@/lib/api/client'
import { useTranslation } from 'react-i18next'

export function CollectionsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [editing, setEditing] = useState<Collection | null>(null)
  const { t } = useTranslation()

  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })
  const overviewQuery = useQuery({
    queryKey: ['collections-overview'],
    queryFn: async () => (await collectionsApi.overview()).data,
  })

  const createCollection = useMutation({
    mutationFn: (payload: {
      name: string
      description?: string
      channel_ids?: string[]
      is_global?: boolean
      is_default?: boolean
      color?: string
      icon?: string
      auto_assign_languages?: string[]
      auto_assign_keywords?: string[]
      auto_assign_tags?: string[]
    }) => collectionsApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections'] }),
  })

  const updateCollection = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string
      payload: {
        name: string
        description?: string
        channel_ids?: string[]
        is_global?: boolean
        is_default?: boolean
        color?: string
        icon?: string
        auto_assign_languages?: string[]
        auto_assign_keywords?: string[]
        auto_assign_tags?: string[]
      }
    }) => collectionsApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections'] }),
  })

  const deleteCollection = useMutation({
    mutationFn: (id: string) => collectionsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections'] }),
  })

  const collections = collectionsQuery.data ?? []

  return (
    <PageTransition>
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-foreground/60">{t('collections.subtitle')}</p>
            <h2 className="text-2xl font-semibold">{t('collections.title')}</h2>
          </div>
          <CollectionManager
            collection={editing}
            onSubmit={async (payload) => {
              if (editing) {
                await updateCollection.mutateAsync({ id: editing.id, payload })
                setEditing(null)
                return
              }
              await createCollection.mutateAsync(payload)
            }}
          />
        </div>
        {collections.length === 0 && !collectionsQuery.isLoading ? (
          <EmptyState
            icon={Layers}
            title={t('collections.emptyTitle')}
            description={t('collections.emptyDescription')}
          />
        ) : (
          <div className="space-y-4">
            {overviewQuery.data?.collections?.length ? (
              <div className="grid gap-4 md:grid-cols-3">
                {overviewQuery.data.collections.map((item) => (
                  <Card key={item.id} className="border border-border/60">
                    <CardContent className="py-5">
                      <p className="text-sm font-semibold">{item.name}</p>
                      <p className="text-xs text-foreground/60">
                        {t('collections.statsMessages7d', { count: item.message_count_7d })}
                      </p>
                      <p className="text-xs text-foreground/60">
                        {t('collections.channelsCount', { count: item.channel_count })}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : null}
            {collections.map((collection) => (
              <CollectionCard
                key={collection.id}
                collection={collection}
                onView={(id) => navigate(`/collections/${id}`)}
                onEdit={(value) => setEditing(value)}
                onDelete={(id) => deleteCollection.mutate(id)}
              />
            ))}
          </div>
        )}
      </div>
    </PageTransition>
  )
}
