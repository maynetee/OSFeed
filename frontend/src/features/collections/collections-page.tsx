import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { CollectionCard } from '@/components/collections/collection-card'
import { CollectionManager } from '@/components/collections/collection-manager'
import { EmptyState } from '@/components/common/empty-state'
import { collectionsApi, type Collection } from '@/lib/api/client'

export function CollectionsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [editing, setEditing] = useState<Collection | null>(null)

  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })

  const createCollection = useMutation({
    mutationFn: (payload: { name: string; description?: string }) =>
      collectionsApi.create({ ...payload, channel_ids: [] }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections'] }),
  })

  const updateCollection = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { name: string; description?: string } }) =>
      collectionsApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections'] }),
  })

  const deleteCollection = useMutation({
    mutationFn: (id: string) => collectionsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collections'] }),
  })

  const collections = collectionsQuery.data ?? []

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-foreground/60">Organisez vos sources</p>
          <h2 className="text-2xl font-semibold">Collections</h2>
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
          title="Aucune collection"
          description="Regroupez vos canaux par thematique."
        />
      ) : (
        <div className="space-y-4">
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
  )
}
