import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useMemo, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { KpiCard } from '@/components/stats/kpi-card'
import { TrendChart } from '@/components/stats/trend-chart'
import { ChannelRanking } from '@/components/stats/channel-ranking'
import { EmptyState } from '@/components/common/empty-state'
import { statsApi, channelsApi, collectionsApi } from '@/lib/api/client'

export function DashboardPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [selectedCollection, setSelectedCollection] = useState<string>('all')

  const channelsQuery = useQuery({
    queryKey: ['channels'],
    queryFn: async () => (await channelsApi.list()).data,
  })
  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })

  const dashboardQuery = useQuery({
    queryKey: ['stats-dashboard', selectedCollection],
    queryFn: async () => {
      const collectionId = selectedCollection === 'all' ? undefined : selectedCollection
      return (await statsApi.dashboard(collectionId)).data
    },
    enabled: selectedCollection === 'all'
      ? (channelsQuery.data?.length ?? 0) > 0
      : selectedCollection !== '',
  })

  const collectionStatsQuery = useQuery({
    queryKey: ['collections', selectedCollection, 'stats'],
    queryFn: async () => (await collectionsApi.stats(selectedCollection)).data,
    enabled: selectedCollection !== 'all',
  })

  const collectionOptions = useMemo(
    () => collectionsQuery.data ?? [],
    [collectionsQuery.data],
  )

  // All hooks must be called before any early returns
  const channels = channelsQuery.data ?? []
  const dashboardData = dashboardQuery.data
  const collectionStats = collectionStatsQuery.data
  const hasNoChannels = channelsQuery.isSuccess && channels.length === 0
  const hasNoCollectionChannels = selectedCollection !== 'all'
    && collectionStatsQuery.isSuccess
    && (collectionStats?.channel_count ?? 0) === 0

  // Show empty state when no sources are configured.
  if (hasNoChannels || hasNoCollectionChannels) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <EmptyState
          title={t('dashboard.emptyTitle')}
          description={t('dashboard.emptyDescription')}
          actionLabel={t('dashboard.emptyAction')}
          onAction={() => navigate('/channels?add=true')}
        />
      </div>
    )
  }

  const kpiMessages = selectedCollection === 'all'
    ? dashboardData?.overview?.messages_last_24h ?? 0
    : collectionStats?.message_count_24h ?? 0
  const kpiDuplicates = selectedCollection === 'all'
    ? Math.round(
        ((dashboardData?.overview?.duplicates_last_24h ?? 0) / ((dashboardData?.overview?.messages_last_24h ?? 0) || 1)) * 100,
      )
    : Math.round((collectionStats?.duplicate_rate ?? 0) * 100)
  const kpiChannels = selectedCollection === 'all'
    ? dashboardData?.overview?.active_channels ?? 0
    : collectionStats?.channel_count ?? 0

  const trendData = selectedCollection === 'all'
    ? dashboardData?.messages_by_day ?? []
    : collectionStats?.activity_trend ?? []

  const topChannels = selectedCollection === 'all'
    ? dashboardData?.messages_by_channel ?? []
    : (collectionStats?.top_channels ?? [])

  const trustStats = dashboardData?.trust_stats

  return (
    <div className="flex flex-col gap-8">
      <fieldset>
        <legend className="text-xs font-semibold uppercase text-foreground/40">
          {t('collections.title')}
        </legend>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant={selectedCollection === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedCollection('all')}
            aria-pressed={selectedCollection === 'all'}
          >
            {t('collections.allCollections')}
          </Button>
          {collectionOptions.map((collection) => (
            <Button
              key={collection.id}
              variant={selectedCollection === collection.id ? 'secondary' : 'outline'}
              size="sm"
              onClick={() => setSelectedCollection(collection.id)}
              aria-pressed={selectedCollection === collection.id}
            >
              {collection.name}
            </Button>
          ))}
        </div>
      </fieldset>
      <section className="grid gap-4 md:grid-cols-3">
        <KpiCard
          label={t('dashboard.kpiMessages')}
          value={Number.isFinite(kpiMessages) ? kpiMessages.toLocaleString() : '--'}
        />
        <KpiCard
          label={t('dashboard.kpiDuplicates')}
          value={Number.isFinite(kpiDuplicates) ? `${kpiDuplicates}%` : '--'}
        />
        <KpiCard
          label={t('dashboard.kpiChannels')}
          value={Number.isFinite(kpiChannels) ? kpiChannels.toLocaleString() : '--'}
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t('dashboard.trustTitle')}</CardTitle>
            <p className="text-sm text-foreground/60">{t('dashboard.trustSubtitle')}</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span>{t('dashboard.trustPrimary')}</span>
              <span className="font-semibold">
                {typeof trustStats?.primary_sources_rate === 'number'
                  ? `${trustStats.primary_sources_rate}%`
                  : '--'}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>{t('dashboard.trustPropaganda')}</span>
              <span className="font-semibold text-warning">
                {typeof trustStats?.propaganda_rate === 'number'
                  ? `${trustStats.propaganda_rate}%`
                  : '--'}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>{t('dashboard.trustVerified')}</span>
              <span className="font-semibold">
                {typeof trustStats?.verified_channels === 'number'
                  ? trustStats.verified_channels.toLocaleString()
                  : '--'}
              </span>
            </div>
            <Button className="w-full" variant="secondary">
              {t('dashboard.trustAction')}
            </Button>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t('dashboard.activityTitle')}</CardTitle>
            <p className="text-sm text-foreground/60">{t('dashboard.activitySubtitle')}</p>
          </CardHeader>
          <CardContent>
            <TrendChart data={trendData} />
          </CardContent>
        </Card>
        <ChannelRanking data={topChannels} />
      </section>
    </div>
  )
}
