import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { collectionsApi } from '@/lib/api/client'
import { Card, CardContent } from '@/components/ui/card'

export function CollectionDetailPage() {
  const { id } = useParams()

  const collectionQuery = useQuery({
    queryKey: ['collections', id],
    queryFn: async () => (await collectionsApi.list()).data.find((collection) => collection.id === id),
    enabled: Boolean(id),
  })

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardContent className="py-6">
          <div className="flex flex-col gap-2">
            <p className="text-sm text-foreground/60">Collection</p>
            <h2 className="text-2xl font-semibold">
              {collectionQuery.data?.name ?? 'Chargement...'}
            </h2>
            <p className="text-sm text-foreground/60">
              {collectionQuery.data?.description ?? 'Aucune description'}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
