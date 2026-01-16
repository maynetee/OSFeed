import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

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
  const { t } = useTranslation()

  const digestQuery = useInfiniteQuery({
    queryKey: ['digests', 'list'],
    initialPageParam: 0,
    queryFn: async ({ pageParam }) =>
      (await summariesApi.list({ limit: 5, offset: pageParam })).data,
    getNextPageParam: (lastPage) => {
      const nextOffset = lastPage.page * lastPage.page_size
      return nextOffset < lastPage.total ? nextOffset : undefined
    },
  })

  const generateDigest = useMutation({
    mutationFn: () => summariesApi.generate(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['digests', 'list'] }),
  })

  const digests = useMemo(
    () => digestQuery.data?.pages.flatMap((page) => page.summaries) ?? [],
    [digestQuery.data],
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-foreground/60">{t('digests.subtitle')}</p>
          <h2 className="text-2xl font-semibold">{t('digests.title')}</h2>
        </div>
        <Button onClick={() => generateDigest.mutate()} disabled={generateDigest.isPending}>
          {generateDigest.isPending ? t('digests.generating') : t('digests.generate')}
        </Button>
      </div>
      {digests.length ? (
        <div className="flex flex-col gap-4">
          {digests.map((digest) => (
            <DigestCard
              key={digest.id}
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
          ))}
          {digestQuery.hasNextPage ? (
            <Button
              variant="outline"
              onClick={() => digestQuery.fetchNextPage()}
              disabled={digestQuery.isFetchingNextPage}
            >
              {digestQuery.isFetchingNextPage ? t('messages.loadingMore') : t('digests.loadMore')}
            </Button>
          ) : null}
        </div>
      ) : digestQuery.isLoading ? (
        <p className="text-sm text-foreground/60">{t('digests.loading')}</p>
      ) : (
        <EmptyState title={t('digests.emptyTitle')} description={t('digests.emptyDescription')} />
      )}
    </div>
  )
}
