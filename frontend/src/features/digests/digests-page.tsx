import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { DigestCard } from '@/components/digests/digest-card'
import { EmptyState } from '@/components/common/empty-state'
import { Button } from '@/components/ui/button'
import { summariesApi } from '@/lib/api/client'

const downloadBlob = (data: Blob, filename: string) => {
  const url = window.URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

export function DigestsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const digestQuery = useQuery({
    queryKey: ['digests'],
    queryFn: async () => (await summariesApi.getDaily()).data,
  })

  const generateDigest = useMutation({
    mutationFn: () => summariesApi.generate(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['digests'] }),
  })

  const digest = digestQuery.data

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-foreground/60">Historique des digests</p>
          <h2 className="text-2xl font-semibold">Daily Digest</h2>
        </div>
        <Button onClick={() => generateDigest.mutate()} disabled={generateDigest.isPending}>
          {generateDigest.isPending ? 'Generation...' : 'Generer nouveau digest'}
        </Button>
      </div>
      {digest ? (
        <DigestCard
          digest={digest}
          onOpen={(id) => navigate(`/digests/${id}`)}
          onExportPdf={async (id) => {
            const response = await summariesApi.exportPdf(id)
            downloadBlob(response.data, `digest-${id}.pdf`)
          }}
          onExportHtml={async (id) => {
            const response = await summariesApi.exportHtml(id)
            downloadBlob(new Blob([response.data], { type: 'text/html' }), `digest-${id}.html`)
          }}
        />
      ) : (
        <EmptyState title="Aucun digest" description="Generez un digest pour commencer." />
      )}
    </div>
  )
}
