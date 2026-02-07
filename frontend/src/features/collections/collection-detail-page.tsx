import { useCallback, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { RefreshCw, Sparkles } from 'lucide-react'

import { collectionsApi, messagesApi } from '@/lib/api/client'
import type { Collection } from '@/lib/api/client'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { MessageFeed } from '@/components/messages/message-feed'
import { CollectionStats } from '@/components/collections/collection-stats'
import { CollectionManager } from '@/components/collections/collection-manager'
import { CollectionExportDialog } from '@/components/collections/collection-export-dialog'
import { CollectionAlerts } from '@/components/collections/collection-alerts'
import { CollectionShares } from '@/components/collections/collection-shares'
import { Timestamp } from '@/components/common/timestamp'
import { cn } from '@/lib/cn'
import { useMessagePolling } from '@/hooks/use-message-polling'
import { SummaryGenerateModal } from '@/features/summaries/summary-generate-modal'

export function CollectionDetailPage() {
  const { id } = useParams()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [exportOpen, setExportOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [summaryOpen, setSummaryOpen] = useState(false)

  const collectionQuery = useQuery({
    queryKey: ['collections', id],
    queryFn: async () => (await collectionsApi.get(id as string)).data,
    enabled: Boolean(id),
  })

  const statsQuery = useQuery({
    queryKey: ['collections', id, 'stats'],
    queryFn: async () => (await collectionsApi.stats(id as string)).data,
    enabled: Boolean(id),
  })

  const messagesQuery = useInfiniteQuery({
    queryKey: ['collection-messages', id],
    initialPageParam: 0,
    queryFn: async ({ pageParam }) => {
      const channelIds = collectionQuery.data?.channel_ids ?? []
      return (
        await messagesApi.list({
          limit: 20,
          offset: pageParam,
          channel_ids: channelIds.length ? channelIds : undefined,
        })
      ).data
    },
    getNextPageParam: (lastPage) => {
      const nextOffset = lastPage.page * lastPage.page_size
      return nextOffset < lastPage.total ? nextOffset : undefined
    },
    enabled: Boolean(collectionQuery.data?.channel_ids?.length),
  })

  const updateCollection = useMutation({
    mutationFn: (payload: Parameters<typeof collectionsApi.update>[1]) =>
      collectionsApi.update(id as string, payload),
    onMutate: async (payload) => {
      await queryClient.cancelQueries({ queryKey: ['collections'] })
      await queryClient.cancelQueries({ queryKey: ['collections', id] })

      const previousCollections = queryClient.getQueryData<Collection[]>(['collections'])
      const previousCollection = queryClient.getQueryData<Collection>(['collections', id])

      if (previousCollections) {
        queryClient.setQueryData<Collection[]>(
          ['collections'],
          previousCollections.map((collection) =>
            collection.id === id ? { ...collection, ...payload } : collection,
          ),
        )
      }

      if (previousCollection) {
        queryClient.setQueryData<Collection>(['collections', id], {
          ...previousCollection,
          ...payload,
        })
      }

      return { previousCollections, previousCollection }
    },
    onError: (_error, _payload, context) => {
      if (context?.previousCollections) {
        queryClient.setQueryData(['collections'], context.previousCollections)
      }
      if (context?.previousCollection) {
        queryClient.setQueryData(['collections', id], context.previousCollection)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
      queryClient.invalidateQueries({ queryKey: ['collections', id] })
      queryClient.invalidateQueries({ queryKey: ['collections', id, 'stats'] })
    },
  })

  const deleteCollection = useMutation({
    mutationFn: () => collectionsApi.delete(id as string),
    onSuccess: () => navigate('/collections'),
  })

  const messages = useMemo(
    () => messagesQuery.data?.pages.flatMap((page) => page.messages) ?? [],
    [messagesQuery.data],
  )

  const downloadBlob = (data: Blob, filename: string) => {
    const url = window.URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    window.URL.revokeObjectURL(url)
  }

  const refetchMessages = useCallback(() => messagesQuery.refetch(), [messagesQuery.refetch])

  const { lastRefreshFormatted, lastRefreshFull, isRefreshing, manualRefresh } = useMessagePolling(
    refetchMessages,
    {
      interval: 20_000,
      enabled: Boolean(collectionQuery.data?.channel_ids?.length),
    }
  )

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-4 py-6">
          <div className="flex flex-col gap-2">
            <p className="text-sm text-foreground/60">{t('collections.title')}</p>
            <h2 className="text-2xl font-semibold">
              {collectionQuery.data?.name ?? t('common.loading')}
            </h2>
            <p className="text-sm text-foreground/60">
              {collectionQuery.data?.description ?? t('collections.emptyDescriptionLabel')}
            </p>
            {collectionQuery.data?.created_at ? (
              <p className="text-xs text-foreground/50">
                {t('collections.createdAt')} <Timestamp value={collectionQuery.data.created_at} />
              </p>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => setEditing(true)}>
              {t('collections.edit')}
            </Button>
            <Button variant="outline" onClick={() => setExportOpen(true)}>
              {t('collections.export')}
            </Button>
            <Button variant="outline" className="gap-1.5" onClick={() => setSummaryOpen(true)}>
              <Sparkles className="h-4 w-4" />
              {t('summaries.generate')}
            </Button>
            <Button variant="outline" onClick={() => deleteCollection.mutate()}>
              {t('collections.delete')}
            </Button>
          </div>
        </CardContent>
      </Card>

      <CollectionStats stats={statsQuery.data} isLoading={statsQuery.isLoading} />

      <Card>
        <CardContent className="py-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-lg font-semibold">{t('collections.feedTitle')}</h3>
            <div className="flex flex-wrap items-center gap-3">
              <div
                className="text-xs text-foreground/60 sm:text-sm"
                title={lastRefreshFull ?? undefined}
              >
                {t('feed.lastRefresh')}{' '}
                <span className="font-mono font-semibold text-foreground/80">
                  {lastRefreshFormatted}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => manualRefresh(collectionQuery.data?.channel_ids ?? [])}
                disabled={isRefreshing}
                className="gap-2"
              >
                <RefreshCw className={cn('h-4 w-4', isRefreshing && 'animate-spin')} />
                <span className="hidden sm:inline">{t('feed.refresh')}</span>
              </Button>
            </div>
          </div>
          <div className="mt-4">
            <MessageFeed
              messages={messages}
              isLoading={messagesQuery.isLoading}
              isFetchingNextPage={messagesQuery.isFetchingNextPage}
              onEndReached={() => {
                if (messagesQuery.hasNextPage) {
                  messagesQuery.fetchNextPage()
                }
              }}
            />
          </div>
        </CardContent>
      </Card>

      {id ? <CollectionAlerts collectionId={id} /> : null}
      {id ? <CollectionShares collectionId={id} /> : null}

      <CollectionManager
        collection={editing ? collectionQuery.data : null}
        hideTrigger
        onSubmit={async (payload) => {
          await updateCollection.mutateAsync(payload)
          setEditing(false)
        }}
      />
      <SummaryGenerateModal
        open={summaryOpen}
        onOpenChange={setSummaryOpen}
        collectionId={id}
      />
      <CollectionExportDialog
        open={exportOpen}
        onOpenChange={setExportOpen}
        onExport={async (params) => {
          const response = await collectionsApi.exportMessages(id as string, params)
          if (params.format === 'pdf') {
            downloadBlob(response.data, `collection-${id}.pdf`)
            return
          }
          if (params.format === 'html') {
            downloadBlob(new Blob([response.data], { type: 'text/html' }), `collection-${id}.html`)
            return
          }
          downloadBlob(new Blob([response.data], { type: 'text/csv' }), `collection-${id}.csv`)
        }}
      />
    </div>
  )
}
