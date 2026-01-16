import { useMemo, useState } from 'react'
import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { subDays } from 'date-fns'
import { useTranslation } from 'react-i18next'

import { ExportDialog } from '@/components/exports/export-dialog'
import { MessageFeed } from '@/components/messages/message-feed'
import { MessageFilters } from '@/components/messages/message-filters'
import { Button } from '@/components/ui/button'
import { channelsApi, collectionsApi, messagesApi } from '@/lib/api/client'
import { useFilterStore } from '@/stores/filter-store'

export function FeedPage() {
  const channelIds = useFilterStore((state) => state.channelIds)
  const dateRange = useFilterStore((state) => state.dateRange)
  const collectionIds = useFilterStore((state) => state.collectionIds)
  const [exportOpen, setExportOpen] = useState(false)
  const { t } = useTranslation()

  const channelsQuery = useQuery({
    queryKey: ['channels'],
    queryFn: async () => (await channelsApi.list()).data,
  })

  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })

  const rangeDays = dateRange === '24h' ? 1 : dateRange === '7d' ? 7 : 30

  const activeChannelIds = useMemo(() => {
    const collectionChannelIds =
      collectionsQuery.data
        ?.filter((collection) => collectionIds.includes(collection.id))
        .flatMap((collection) => collection.channel_ids) ?? []
    return Array.from(new Set([...channelIds, ...collectionChannelIds]))
  }, [collectionsQuery.data, collectionIds, channelIds])

  const messagesQuery = useInfiniteQuery({
    queryKey: ['messages', activeChannelIds, dateRange],
    initialPageParam: 0,
    queryFn: async ({ pageParam }) => {
      return (
        await messagesApi.list({
          limit: 20,
          offset: pageParam,
          channel_ids: activeChannelIds.length ? activeChannelIds : undefined,
          start_date: subDays(new Date(), rangeDays).toISOString(),
        })
      ).data
    },
    getNextPageParam: (lastPage) => {
      const nextOffset = lastPage.page * lastPage.page_size
      return nextOffset < lastPage.total ? nextOffset : undefined
    },
  })

  const messages = useMemo(
    () => messagesQuery.data?.pages.flatMap((page) => page.messages) ?? [],
    [messagesQuery.data],
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-foreground/60">{t('feed.subtitle')}</p>
          <h2 className="text-2xl font-semibold">{t('feed.title')}</h2>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">{t('feed.filters')}</Button>
          <Button onClick={() => setExportOpen(true)}>{t('feed.export')}</Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_3fr]">
        <MessageFilters
          channels={(channelsQuery.data ?? []).map((channel) => ({
            id: channel.id,
            title: channel.title,
          }))}
          collections={(collectionsQuery.data ?? []).map((collection) => ({
            id: collection.id,
            name: collection.name,
          }))}
        />
        <div className="flex flex-col gap-4">
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
      </div>

      <ExportDialog
        open={exportOpen}
        onOpenChange={setExportOpen}
        filters={{
          channel_ids: activeChannelIds.length ? activeChannelIds : undefined,
          start_date: subDays(new Date(), rangeDays).toISOString(),
        }}
      />
    </div>
  )
}
