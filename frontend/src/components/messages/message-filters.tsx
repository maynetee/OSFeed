import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useFilterStore } from '@/stores/filter-store'

interface MessageFiltersProps {
  channels: { id: string; title: string }[]
  collections: { id: string; name: string }[]
}

export function MessageFilters({ channels, collections }: MessageFiltersProps) {
  const channelIds = useFilterStore((state) => state.channelIds)
  const dateRange = useFilterStore((state) => state.dateRange)
  const collectionIds = useFilterStore((state) => state.collectionIds)
  const setChannelIds = useFilterStore((state) => state.setChannelIds)
  const setCollectionIds = useFilterStore((state) => state.setCollectionIds)
  const setDateRange = useFilterStore((state) => state.setDateRange)
  const { t } = useTranslation()

  const channelOptions = useMemo(
    () => channels.map((channel) => ({ id: channel.id, title: channel.title })),
    [channels],
  )
  const collectionOptions = useMemo(
    () => collections.map((collection) => ({ id: collection.id, name: collection.name })),
    [collections],
  )

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 py-6">
        <div>
          <p className="text-sm font-semibold">{t('filters.title')}</p>
          <p className="text-xs text-foreground/60">{t('filters.subtitle')}</p>
        </div>

        <p className="text-xs font-semibold uppercase text-foreground/40">{t('filters.period')}</p>
        <div className="flex flex-wrap gap-2">
          {['24h', '7d', '30d'].map((range) => (
            <Button
              key={range}
              variant={dateRange === range ? 'default' : 'outline'}
              size="sm"
              onClick={() => setDateRange(range as '24h' | '7d' | '30d')}
            >
              {range}
            </Button>
          ))}
        </div>

        <p className="text-xs font-semibold uppercase text-foreground/40">{t('filters.channels')}</p>
        <div className="flex flex-wrap gap-2">
          {channelOptions.map((channel) => {
            const active = channelIds.includes(channel.id)
            return (
              <Button
                key={channel.id}
                variant={active ? 'secondary' : 'outline'}
                size="sm"
                onClick={() =>
                  setChannelIds(
                    active
                      ? channelIds.filter((id) => id !== channel.id)
                      : [...channelIds, channel.id],
                  )
                }
              >
                {channel.title}
              </Button>
            )
          })}
        </div>

        {collectionOptions.length ? (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase text-foreground/40">
              {t('filters.collections')}
            </p>
            <div className="flex flex-wrap gap-2">
            {collectionOptions.map((collection) => {
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
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
