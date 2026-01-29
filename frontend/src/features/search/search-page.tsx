import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { MessageFeed } from '@/components/messages/message-feed'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { collectionsApi, messagesApi } from '@/lib/api/client'

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [activeTab, setActiveTab] = useState('keyword')
  const [collectionIds, setCollectionIds] = useState<string[]>([])
  const { t } = useTranslation()

  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })

  const searchChannelIds = useMemo(() => {
    if (!collectionIds.length) return undefined
    const ids =
      collectionsQuery.data
        ?.filter((collection) => collectionIds.includes(collection.id))
        .flatMap((collection) => collection.channel_ids) ?? []
    return ids.length ? Array.from(new Set(ids)) : undefined
  }, [collectionsQuery.data, collectionIds])

  const keywordQuery = useQuery({
    queryKey: ['search', 'keyword', query, searchChannelIds],
    queryFn: async () =>
      (
        await messagesApi.search({
          q: query,
          limit: 20,
          offset: 0,
          channel_ids: searchChannelIds,
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

  return (
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
      <div className="flex flex-wrap gap-2">
        <Button
          variant={!collectionIds.length ? 'default' : 'outline'}
          size="sm"
          onClick={() => setCollectionIds([])}
        >
          {t('collections.allCollections')}
        </Button>
        {(collectionsQuery.data ?? []).map((collection) => {
          const active = collectionIds.includes(collection.id)
          return (
            <Button
              key={collection.id}
              variant={active ? 'secondary' : 'outline'}
              size="sm"
              onClick={() =>
                setCollectionIds(
                  active
                    ? collectionIds.filter((id) => id !== collection.id)
                    : [...collectionIds, collection.id],
                )
              }
            >
              {collection.name}
            </Button>
          )
        })}
      </div>

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
  )
}
