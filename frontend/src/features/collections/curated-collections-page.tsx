import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { CuratedCollectionCard } from '@/components/collections/curated-collection-card'
import { EmptyState } from '@/components/common/empty-state'
import { Input } from '@/components/ui/input'
import { curatedCollectionsApi } from '@/lib/api/client'

const REGIONS = ['Europe', 'Middle East', 'Asia-Pacific', 'Americas', 'Africa', 'Global']
const TOPICS = ['Conflict', 'Politics', 'Cybersecurity', 'Security', 'Geopolitics', 'Defense', 'Economy', 'Humanitarian', 'Information']

export function CuratedCollectionsPage() {
  const { t } = useTranslation()
  const [region, setRegion] = useState('')
  const [topic, setTopic] = useState('')
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['curated-collections', region, topic, search],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (region) params.region = region
      if (topic) params.topic = topic
      if (search) params.search = search
      return (await curatedCollectionsApi.list(params)).data
    },
  })

  const collections = data ?? []

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-sm text-foreground/60">{t('curatedCollections.subtitle')}</p>
        <h2 className="text-2xl font-semibold">{t('curatedCollections.title')}</h2>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select
          className="h-10 rounded-md border border-border bg-background px-3 text-sm text-foreground"
          value={region}
          onChange={(e) => setRegion(e.target.value)}
        >
          <option value="">{t('curatedCollections.allRegions')}</option>
          {REGIONS.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>

        <select
          className="h-10 rounded-md border border-border bg-background px-3 text-sm text-foreground"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        >
          <option value="">{t('curatedCollections.allTopics')}</option>
          {TOPICS.map((tp) => (
            <option key={tp} value={tp}>{tp}</option>
          ))}
        </select>

        <Input
          className="max-w-xs"
          placeholder={t('curatedCollections.search')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl border border-border bg-muted" />
          ))}
        </div>
      ) : collections.length === 0 ? (
        <EmptyState
          title={t('curatedCollections.title')}
          description={t('curatedCollections.subtitle')}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {collections.map((collection) => (
            <CuratedCollectionCard key={collection.id} collection={collection} />
          ))}
        </div>
      )}
    </div>
  )
}
