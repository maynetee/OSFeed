import { useCallback, useEffect, useMemo, useState } from 'react'
import { useInfiniteQuery, useQuery, useQueryClient, InfiniteData } from '@tanstack/react-query'
import { subDays } from 'date-fns'
import { useTranslation } from 'react-i18next'
import { RefreshCw, Radio, Sparkles, AlertTriangle } from 'lucide-react'

import { ExportDialog } from '@/components/exports/export-dialog'
import { MessageFeed } from '@/components/messages/message-feed'
import { MessageFilters } from '@/components/messages/message-filters'
import { Button } from '@/components/ui/button'
import { channelsApi, collectionsApi, messagesApi, MessageListResponse, TranslationUpdate } from '@/lib/api/client'
import { cn } from '@/lib/cn'
import { useMessageStream } from '@/hooks/use-message-stream'
import { useFilterStore } from '@/stores/filter-store'
import { SummaryGenerateModal } from '@/features/summaries/summary-generate-modal'

type FeedQueryData = InfiniteData<MessageListResponse>

export function FeedPage() {
  const queryClient = useQueryClient()
  const channelIds = useFilterStore((state) => state.channelIds)
  const dateRange = useFilterStore((state) => state.dateRange)
  const collectionIds = useFilterStore((state) => state.collectionIds)
  const mediaTypes = useFilterStore((state) => state.mediaTypes)
  const region = useFilterStore((state) => state.region)
  const topic = useFilterStore((state) => state.topic)
  const setChannelIds = useFilterStore((state) => state.setChannelIds)
  const setCollectionIds = useFilterStore((state) => state.setCollectionIds)
  const filtersTouched = useFilterStore((state) => state.filtersTouched)
  const resetFilters = useFilterStore((state) => state.resetFilters)
  const uniqueOnly = useFilterStore((state) => state.uniqueOnly)
  const setUniqueOnly = useFilterStore((state) => state.setUniqueOnly)
  const highEscalationOnly = useFilterStore((state) => state.highEscalationOnly)
  const setHighEscalationOnly = useFilterStore((state) => state.setHighEscalationOnly)
  const [exportOpen, setExportOpen] = useState(false)
  const [summaryOpen, setSummaryOpen] = useState(false)
  const [sort, setSort] = useState<'latest' | 'relevance'>('latest')
  const { t } = useTranslation()
  const [lastMessageTime, setLastMessageTime] = useState<Date | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const channelsQuery = useQuery({
    queryKey: ['channels'],
    queryFn: async () => (await channelsApi.list()).data,
  })

  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })

  const rangeDays = dateRange === '24h' ? 1 : dateRange === '7d' ? 7 : dateRange === '30d' ? 30 : null

  const activeChannelIds = useMemo(() => {
    const availableChannelIds = new Set((channelsQuery.data ?? []).map((channel) => channel.id))
    const availableCollectionIds = new Set((collectionsQuery.data ?? []).map((collection) => collection.id))
    const validChannelIds = channelIds.filter((id) => availableChannelIds.has(id))
    const validCollectionIds = collectionIds.filter((id) => availableCollectionIds.has(id))
    const collectionChannelIds =
      collectionsQuery.data
        ?.filter((collection) => validCollectionIds.includes(collection.id))
        .flatMap((collection) => collection.channel_ids) ?? []
    const scopedIds = [...validChannelIds, ...collectionChannelIds].filter((id) =>
      availableChannelIds.has(id),
    )
    return Array.from(new Set(scopedIds))
  }, [channelsQuery.data, collectionsQuery.data, channelIds, collectionIds])

  useEffect(() => {
    const availableChannelIds = new Set((channelsQuery.data ?? []).map((channel) => channel.id))
    const nextChannelIds = channelIds.filter((id) => availableChannelIds.has(id))
    if (nextChannelIds.length !== channelIds.length) {
      setChannelIds(nextChannelIds)
    }

    const availableCollectionIds = new Set((collectionsQuery.data ?? []).map((collection) => collection.id))
    const nextCollectionIds = collectionIds.filter((id) => availableCollectionIds.has(id))
    if (nextCollectionIds.length !== collectionIds.length) {
      setCollectionIds(nextCollectionIds)
    }

    if (!filtersTouched && (channelIds.length > 0 || collectionIds.length > 0)) {
      resetFilters()
    }
  }, [channelsQuery.data, collectionsQuery.data, channelIds, collectionIds, filtersTouched, resetFilters, setChannelIds, setCollectionIds])

  const messagesQuery = useInfiniteQuery({
    queryKey: ['messages', activeChannelIds, dateRange, mediaTypes, sort, region, topic, uniqueOnly, highEscalationOnly],
    initialPageParam: 0,
    queryFn: async ({ pageParam }) => {
      return (
        await messagesApi.list({
          limit: 20,
          offset: pageParam,
          channel_ids: activeChannelIds.length ? activeChannelIds : undefined,
          start_date: rangeDays ? subDays(new Date(), rangeDays).toISOString() : undefined,
          media_types: mediaTypes.length ? mediaTypes : undefined,
          sort,
          region: region || undefined,
          topics: topic ? [topic] : undefined,
          unique_only: uniqueOnly || undefined,
          min_escalation: highEscalationOnly ? 0.7 : undefined,
        })
      ).data
    },
    getNextPageParam: (lastPage) => {
      const nextOffset = lastPage.page * lastPage.page_size
      return nextOffset < lastPage.total ? nextOffset : undefined
    },
  })

  const handleTranslation = useCallback((update: TranslationUpdate) => {
    // Update the message in the query cache
    queryClient.setQueryData<FeedQueryData>(['messages', activeChannelIds, dateRange, mediaTypes, sort, region, topic, uniqueOnly, highEscalationOnly], (oldData) => {
      if (!oldData?.pages) return oldData

      return {
        ...oldData,
        pages: oldData.pages.map((page) => ({
          ...page,
          messages: page.messages.map((msg) =>
            msg.id === update.message_id
              ? {
                  ...msg,
                  translated_text: update.translated_text,
                  source_language: update.source_language,
                  target_language: update.target_language,
                  needs_translation: false,
                }
              : msg
          ),
        })),
      }
    })
  }, [queryClient, activeChannelIds, dateRange, mediaTypes, sort, region, topic, uniqueOnly, highEscalationOnly])

  const { isConnected } = useMessageStream({
    channelIds: activeChannelIds,
    onMessages: (newMessages, isRealtime) => {
      if (isRealtime && newMessages.length > 0) {
        setLastMessageTime(new Date())
        queryClient.setQueryData<FeedQueryData>(['messages', activeChannelIds, dateRange, mediaTypes, sort, region, topic, uniqueOnly, highEscalationOnly], (oldData) => {
          if (!oldData) return oldData
          const newPages = [...oldData.pages]
          if (newPages.length > 0) {
            // Filter out existing messages to avoid duplicates
            const existingIds = new Set(newPages.flatMap((p) => p.messages).map((m) => m.id))
            const uniqueNewMessages = newMessages.filter(m => !existingIds.has(m.id))

            if (uniqueNewMessages.length > 0) {
                newPages[0] = {
                  ...newPages[0],
                  messages: [...uniqueNewMessages, ...newPages[0].messages]
                }
            }
          }
          return {
            ...oldData,
            pages: newPages
          }
        })
      }
    },
    onTranslation: handleTranslation,
  })

  const manualRefresh = async () => {
    setIsRefreshing(true)
    try {
        await channelsApi.refresh(activeChannelIds)
        // Stream will pick up new messages automatically
    } catch (e) {
        console.error(e)
    } finally {
        setIsRefreshing(false)
    }
  }

  const messages = useMemo(
    () => messagesQuery.data?.pages.flatMap((page) => page.messages) ?? [],
    [messagesQuery.data],
  )
  const hasActiveFilters = channelIds.length > 0 || collectionIds.length > 0 || mediaTypes.length > 0 || region !== '' || topic !== ''
  const totalChannels = (channelsQuery.data ?? []).length

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-foreground/60">{t('feed.subtitle')}</p>
          <h2 className="text-2xl font-semibold">{t('feed.title')}</h2>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-foreground/60 sm:text-sm">
            {isConnected ? (
                <span className="flex items-center gap-1.5 text-green-600">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500"></span>
                    </span>
                    Live
                </span>
            ) : (
                <span className="flex items-center gap-1 text-yellow-600">
                    <Radio className="h-3 w-3" />
                    Connecting...
                </span>
            )}
            {lastMessageTime && (
                <span className="text-muted-foreground ml-2">
                    Last update: {lastMessageTime.toLocaleTimeString()}
                </span>
            )}
          </div>
          <Button
            variant="outline"
            onClick={() => manualRefresh()}
            disabled={isRefreshing}
            className="gap-2"
          >
            <RefreshCw className={cn('h-4 w-4', isRefreshing && 'animate-spin')} />
            <span className="hidden sm:inline">{t('feed.refresh')}</span>
          </Button>
          <Button variant="outline" className="gap-1.5" onClick={() => setSummaryOpen(true)}>
            <Sparkles className="h-4 w-4" />
            <span className="hidden sm:inline">{t('summaries.generate')}</span>
          </Button>
          <Button variant="outline">{t('feed.filters')}</Button>
          <Button onClick={() => setExportOpen(true)}>{t('feed.export')}</Button>
        </div>
      </div>

      {hasActiveFilters ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/60 bg-muted/30 px-4 py-2 text-xs text-foreground/70">
          <span>
            {t('filters.active', { count: activeChannelIds.length, total: totalChannels })}
          </span>
          <Button variant="ghost" size="sm" onClick={() => resetFilters()}>
            {t('filters.clear')}
          </Button>
        </div>
      ) : null}

      <div className="flex items-center gap-2">
        <Button
          variant={sort === 'latest' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSort('latest')}
        >
          {t('feed.sortLatest')}
        </Button>
        <Button
          variant={sort === 'relevance' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSort('relevance')}
        >
          {t('feed.sortRelevance')}
        </Button>
        <div className="h-4 w-px bg-border mx-1" />
        <Button variant={!uniqueOnly ? 'default' : 'outline'} size="sm" onClick={() => setUniqueOnly(false)}>
          {t('feed.allMessages')}
        </Button>
        <Button variant={uniqueOnly ? 'default' : 'outline'} size="sm" onClick={() => setUniqueOnly(true)}>
          {t('feed.uniqueStories')}
        </Button>
        <div className="h-4 w-px bg-border mx-1" />
        <Button
          variant={highEscalationOnly ? 'destructive' : 'outline'}
          size="sm"
          onClick={() => setHighEscalationOnly(!highEscalationOnly)}
          className="gap-1.5"
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          {t('analysis.escalation.filterHigh')}
        </Button>
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

      <SummaryGenerateModal
        open={summaryOpen}
        onOpenChange={setSummaryOpen}
        channelIds={activeChannelIds}
      />
      <ExportDialog
        open={exportOpen}
        onOpenChange={setExportOpen}
        filters={{
          channel_ids: activeChannelIds.length ? activeChannelIds : undefined,
          start_date: rangeDays ? subDays(new Date(), rangeDays).toISOString() : undefined,
          media_types: mediaTypes.length ? mediaTypes : undefined,
        }}
      />
    </div>
  )
}
