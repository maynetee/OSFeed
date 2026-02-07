import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { subDays } from 'date-fns'
import { useTranslation } from 'react-i18next'

import { PageTransition } from '@/components/layout/page-transition'
import { MessageFeed } from '@/components/messages/message-feed'
import { MessageFilters } from '@/components/messages/message-filters'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { channelsApi, collectionsApi, messagesApi } from '@/lib/api/client'
import { useFilterStore } from '@/stores/filter-store'

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [activeTab, setActiveTab] = useState('keyword')
  const { t } = useTranslation()
  const channelIds = useFilterStore((state) => state.channelIds)
  const dateRange = useFilterStore((state) => state.dateRange)
  const collectionIds = useFilterStore((state) => state.collectionIds)
  const mediaTypes = useFilterStore((state) => state.mediaTypes)
  const setChannelIds = useFilterStore((state) => state.setChannelIds)
  const setCollectionIds = useFilterStore((state) => state.setCollectionIds)
  const filtersTouched = useFilterStore((state) => state.filtersTouched)
  const resetFilters = useFilterStore((state) => state.resetFilters)

  const channelsQuery = useQuery({
    queryKey: ['channels'],
    queryFn: async () => (await channelsApi.list()).data,
  })

  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })

  const rangeDays =
    dateRange === '24h' ? 1 : dateRange === '7d' ? 7 : dateRange === '30d' ? 30 : null

  const activeChannelIds = useMemo(() => {
    const availableChannelIds = new Set((channelsQuery.data ?? []).map((channel) => channel.id))
    const availableCollectionIds = new Set(
      (collectionsQuery.data ?? []).map((collection) => collection.id),
    )
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

    const availableCollectionIds = new Set(
      (collectionsQuery.data ?? []).map((collection) => collection.id),
    )
    const nextCollectionIds = collectionIds.filter((id) => availableCollectionIds.has(id))
    if (nextCollectionIds.length !== collectionIds.length) {
      setCollectionIds(nextCollectionIds)
    }

    if (!filtersTouched && (channelIds.length > 0 || collectionIds.length > 0)) {
      resetFilters()
    }
  }, [
    channelsQuery.data,
    collectionsQuery.data,
    channelIds,
    collectionIds,
    filtersTouched,
    resetFilters,
    setChannelIds,
    setCollectionIds,
  ])

  const keywordQuery = useQuery({
    queryKey: ['search', 'keyword', query, activeChannelIds, dateRange, mediaTypes],
    queryFn: async () =>
      (
        await messagesApi.search({
          q: query,
          limit: 20,
          offset: 0,
          channel_ids: activeChannelIds.length ? activeChannelIds : undefined,
          start_date: rangeDays ? subDays(new Date(), rangeDays).toISOString() : undefined,
          media_types: mediaTypes.length ? mediaTypes : undefined,
        })
      ).data,
    enabled: query.length > 2,
  })

  const entityResults = useMemo(() => {
    if (query.length < 3) return []
    const normalized = query.toLowerCase()
    return (
      keywordQuery.data?.messages.filter((message) => {
        const entities = message.entities
        if (!entities) return false
        return (
          entities.persons?.some((item) => item.toLowerCase().includes(normalized)) ||
          entities.locations?.some((item) => item.toLowerCase().includes(normalized)) ||
          entities.organizations?.some((item) => item.toLowerCase().includes(normalized))
        )
      }) ?? []
    )
  }, [keywordQuery.data, query])

  const hasActiveFilters =
    channelIds.length > 0 || collectionIds.length > 0 || mediaTypes.length > 0
  const totalChannels = (channelsQuery.data ?? []).length

  return (
    <PageTransition>
      <div className="flex flex-col gap-6">
        <div>
          <p className="text-sm text-foreground/60">{t('search.subtitle')}</p>
          <h2 className="text-2xl font-semibold">{t('search.title')}</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Input
            placeholder={t('search.placeholder')}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label={t('search.placeholder')}
          />
          <Button variant="secondary">{t('search.launch')}</Button>
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
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList>
                <TabsTrigger value="keyword">{t('search.keyword')}</TabsTrigger>
                <TabsTrigger value="entities">{t('search.entities')}</TabsTrigger>
              </TabsList>
              <TabsContent value="keyword">
                {query.length < 3 ? (
                  <Card>
                    <CardContent className="py-10 text-sm text-foreground/60">
                      {t('search.minChars')}
                    </CardContent>
                  </Card>
                ) : (
                  <MessageFeed
                    messages={keywordQuery.data?.messages ?? []}
                    isLoading={keywordQuery.isLoading}
                  />
                )}
              </TabsContent>
              <TabsContent value="entities">
                {query.length < 3 ? (
                  <Card>
                    <CardContent className="py-10 text-sm text-foreground/60">
                      {t('search.minChars')}
                    </CardContent>
                  </Card>
                ) : (
                  <MessageFeed messages={entityResults} isLoading={keywordQuery.isLoading} />
                )}
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
