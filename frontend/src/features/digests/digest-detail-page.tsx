import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { summariesApi } from '@/lib/api/client'
import { DigestViewer } from '@/components/digests/digest-viewer'

export function DigestDetailPage() {
  const { id } = useParams()

  const digestQuery = useQuery({
    queryKey: ['digest', id],
    queryFn: async () => (id ? (await summariesApi.get(id)).data : null),
    enabled: Boolean(id),
  })

  return <DigestViewer digest={digestQuery.data ?? undefined} isLoading={digestQuery.isLoading} />
}
