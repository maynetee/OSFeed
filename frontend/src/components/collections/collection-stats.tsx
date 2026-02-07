import { memo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendChart } from '@/components/stats/trend-chart'
import type { CollectionStats as CollectionStatsData } from '@/lib/api/client'
import { useTranslation } from 'react-i18next'

interface CollectionStatsProps {
  stats?: CollectionStatsData
  isLoading?: boolean
}

export const CollectionStats = memo(function CollectionStats({
  stats,
  isLoading,
}: CollectionStatsProps) {
  const { t } = useTranslation()

  if (isLoading && !stats) {
    return <p className="text-sm text-foreground/60">{t('common.loading')}</p>
  }

  if (!stats) {
    return null
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>{t('collections.statsTitle')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-xl border border-border/60 p-3">
              <p className="text-xs text-foreground/60">{t('collections.statsMessages')}</p>
              <p className="text-xl font-semibold">{stats.message_count.toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-border/60 p-3">
              <p className="text-xs text-foreground/60">{t('collections.statsMessages24h')}</p>
              <p className="text-xl font-semibold">{stats.message_count_24h.toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-border/60 p-3">
              <p className="text-xs text-foreground/60">{t('collections.statsChannels')}</p>
              <p className="text-xl font-semibold">{stats.channel_count.toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-border/60 p-3">
              <p className="text-xs text-foreground/60">{t('collections.statsDuplicateRate')}</p>
              <p className="text-xl font-semibold">{Math.round(stats.duplicate_rate * 100)}%</p>
            </div>
          </div>
          <div className="rounded-xl border border-border/60 p-3">
            <p className="text-xs font-semibold uppercase text-foreground/90">
              {t('collections.statsActivity')}
            </p>
            <TrendChart data={stats.activity_trend} />
          </div>
        </CardContent>
      </Card>
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>{t('collections.topChannels')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {stats.top_channels.length ? (
              stats.top_channels.map((channel) => (
                <div key={channel.channel_id} className="flex items-center justify-between text-sm">
                  <span className="font-medium">{channel.channel_title}</span>
                  <span className="text-foreground/60">{channel.count}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-foreground/60">{t('collections.noStats')}</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{t('collections.languagesTitle')}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {Object.keys(stats.languages).length ? (
              Object.entries(stats.languages).map(([lang, count]) => (
                <Badge key={lang} variant="outline">
                  {lang} · {count}
                </Badge>
              ))
            ) : (
              <p className="text-sm text-foreground/60">{t('collections.noLanguages')}</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
})
