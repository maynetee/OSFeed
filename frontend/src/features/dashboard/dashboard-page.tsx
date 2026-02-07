import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useEffect, useMemo, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { KpiCard } from '@/components/stats/kpi-card'
import { TrendChart } from '@/components/stats/trend-chart'
import { ChannelRanking } from '@/components/stats/channel-ranking'
import { EmptyState } from '@/components/common/empty-state'
import { statsApi, collectionsApi } from '@/lib/api/client'
import { insightsApi } from '@/lib/api/insights'
import type { IntelligenceTip, TrendingTopic, ActivitySpike } from '@/lib/api/insights'

function useAnimatedCounter(target: number, duration = 1500) {
  const [count, setCount] = useState(0)
  const startTime = useRef<number | null>(null)
  const prevTarget = useRef(0)

  useEffect(() => {
    if (target === 0) {
      setCount(0)
      return
    }
    const from = prevTarget.current
    prevTarget.current = target
    startTime.current = null

    let animationId: number
    const animate = (timestamp: number) => {
      if (!startTime.current) startTime.current = timestamp
      const elapsed = timestamp - startTime.current
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCount(Math.floor(from + eased * (target - from)))
      if (progress < 1) {
        animationId = requestAnimationFrame(animate)
      }
    }
    animationId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationId)
  }, [target, duration])

  return count
}

const SEVERITY_COLORS: Record<string, string> = {
  info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  critical: 'bg-red-500/10 text-red-400 border-red-500/20',
}

const SEVERITY_DOT: Record<string, string> = {
  info: 'bg-blue-400',
  warning: 'bg-amber-400',
  critical: 'bg-red-400',
}

export function DashboardPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [selectedCollection, setSelectedCollection] = useState<string>('all')

  const dashboardQuery = useQuery({
    queryKey: ['stats-dashboard', selectedCollection],
    queryFn: async () => {
      const collectionId = selectedCollection === 'all' ? undefined : selectedCollection
      return (await statsApi.dashboard(collectionId)).data
    },
  })

  const collectionStatsQuery = useQuery({
    queryKey: ['collections', selectedCollection, 'stats'],
    queryFn: async () => (await collectionsApi.stats(selectedCollection)).data,
    enabled: selectedCollection !== 'all',
  })

  const insightsQuery = useQuery({
    queryKey: ['insights-dashboard'],
    queryFn: async () => (await insightsApi.dashboard()).data,
    refetchInterval: 300000, // 5 minutes
  })

  // All hooks must be called before any early returns
  const dashboardData = dashboardQuery.data
  const collectionStats = collectionStatsQuery.data
  const insights = insightsQuery.data
  const channels = dashboardData?.channels ?? []
  const collectionOptions = useMemo(
    () => dashboardData?.collections ?? [],
    [dashboardData?.collections],
  )

  const signalCount = useAnimatedCounter(insights?.signals_processed?.all_time ?? 0)

  const hasNoChannels = dashboardQuery.isSuccess && channels.length === 0
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

  const tips: IntelligenceTip[] = insights?.intelligence_tips ?? []
  const topics: TrendingTopic[] = insights?.trending_topics ?? []
  const spikes: ActivitySpike[] = insights?.activity_spikes ?? []

  return (
    <div className="flex flex-col gap-8">
      <fieldset>
        <legend className="text-xs font-semibold uppercase text-foreground/90">
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

      {/* Signal Counter */}
      <section>
        <Card>
          <CardContent className="py-6">
            <div className="flex flex-col items-center gap-2">
              <p className="text-sm font-medium text-muted-foreground">
                {t('dashboard.signalsProcessed')}
              </p>
              <p className="text-4xl font-bold tabular-nums tracking-tight">
                {signalCount.toLocaleString()}
              </p>
              <div className="flex items-center gap-6 text-sm text-muted-foreground">
                <span>
                  {t('dashboard.signalsToday')}: <strong className="text-foreground">{(insights?.signals_processed?.today ?? 0).toLocaleString()}</strong>
                </span>
                <span>
                  {t('dashboard.signalsThisWeek')}: <strong className="text-foreground">{(insights?.signals_processed?.this_week ?? 0).toLocaleString()}</strong>
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Intelligence Insights Row */}
      <section className="grid gap-6 lg:grid-cols-3">
        {/* Intelligence Tips */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{t('dashboard.intelligenceTips')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {tips.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t('dashboard.noTips')}</p>
            ) : (
              tips.map((tip, i) => (
                <div key={i} className={`rounded-lg border p-3 ${SEVERITY_COLORS[tip.severity] || SEVERITY_COLORS.info}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`h-2 w-2 rounded-full ${SEVERITY_DOT[tip.severity] || SEVERITY_DOT.info}`} />
                    <span className="text-sm font-medium">{tip.title}</span>
                  </div>
                  <p className="text-xs opacity-80">{tip.description}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Trending Topics */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{t('dashboard.trendingTopics')}</CardTitle>
            <p className="text-xs text-muted-foreground">{t('dashboard.trendingLast24h')}</p>
          </CardHeader>
          <CardContent>
            {topics.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t('dashboard.noTopics')}</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {topics.map((topic) => (
                  <span
                    key={topic.topic}
                    className="inline-flex items-center gap-1.5 rounded-full border bg-muted/50 px-3 py-1 text-sm"
                  >
                    {topic.topic}
                    <span className="text-xs text-muted-foreground">({topic.count})</span>
                  </span>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Activity Spikes */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{t('dashboard.activitySpikes')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {spikes.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t('dashboard.noSpikes')}</p>
            ) : (
              spikes.slice(0, 5).map((spike) => (
                <div key={spike.channel_id} className="flex items-center justify-between text-sm">
                  <span className="truncate mr-2">{spike.channel_title}</span>
                  <span className="shrink-0 rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-400">
                    {t('dashboard.activitySpikeRatio', { ratio: spike.ratio })}
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </section>

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
