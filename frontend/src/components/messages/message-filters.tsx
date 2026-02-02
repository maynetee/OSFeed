import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useShallow } from 'zustand/react/shallow'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useFilterStore } from '@/stores/filter-store'

interface MessageFiltersProps {
  channels: { id: string; title: string }[]
  collections: { id: string; name: string }[]
}

export function MessageFilters({ channels, collections }: MessageFiltersProps) {
  const {
    channelIds,
    dateRange,
    mediaTypes,
    collectionIds,
    setChannelIds,
    setCollectionIds,
    setDateRange,
    setMediaTypes,
    setFiltersTouched,
    resetFilters,
  } = useFilterStore(
    useShallow((state) => ({
      channelIds: state.channelIds,
      dateRange: state.dateRange,
      mediaTypes: state.mediaTypes,
      collectionIds: state.collectionIds,
      setChannelIds: state.setChannelIds,
      setCollectionIds: state.setCollectionIds,
      setDateRange: state.setDateRange,
      setMediaTypes: state.setMediaTypes,
      setFiltersTouched: state.setFiltersTouched,
      resetFilters: state.resetFilters,
    }))
  )
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
        <div className="flex justify-end">
          {(channelIds.length > 0 || collectionIds.length > 0 || mediaTypes.length > 0) ? (
            <Button variant="ghost" size="sm" onClick={() => resetFilters()}>
              {t('filters.clear')}
            </Button>
          ) : null}
        </div>

        <fieldset>
          <legend className="text-xs font-semibold uppercase text-foreground/70">{t('filters.period')}</legend>
          <div className="flex flex-wrap gap-2">
            {[
              { value: '24h', label: '24h' },
              { value: '7d', label: '7d' },
              { value: '30d', label: '30d' },
              { value: 'all', label: t('filters.all') },
            ].map((range) => (
              <Button
                key={range.value}
                variant={dateRange === range.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => {
                  setFiltersTouched(true)
                  setDateRange(range.value as '24h' | '7d' | '30d' | 'all')
                }}
                aria-pressed={dateRange === range.value}
              >
                {range.label}
              </Button>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend className="text-xs font-semibold uppercase text-foreground/70">{t('filters.mediaTypes')}</legend>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={mediaTypes.length === 0 ? 'default' : 'outline'}
              size="sm"
              onClick={() => {
                setFiltersTouched(true)
                setMediaTypes([])
              }}
              aria-pressed={mediaTypes.length === 0}
            >
              {t('filters.all')}
            </Button>
            {[
              { value: 'text', label: t('filters.text') },
              { value: 'photo', label: t('filters.photo') },
              { value: 'video', label: t('filters.video') },
              { value: 'document', label: t('filters.document') },
            ].map((type) => {
              const active = mediaTypes.includes(type.value)
              return (
                <Button
                  key={type.value}
                  variant={active ? 'secondary' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setFiltersTouched(true)
                    setMediaTypes(
                      active
                        ? mediaTypes.filter((t) => t !== type.value)
                        : [...mediaTypes, type.value]
                    )
                  }}
                  aria-pressed={active}
                >
                  {type.label}
                </Button>
              )
            })}
          </div>
        </fieldset>

        <fieldset>
          <legend className="text-xs font-semibold uppercase text-foreground/70">{t('filters.channels')}</legend>
          <div className="flex flex-wrap gap-2">
            {channelOptions.map((channel) => {
              const active = channelIds.includes(channel.id)
              return (
                <Button
                  key={channel.id}
                  variant={active ? 'secondary' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setFiltersTouched(true)
                    setChannelIds(
                      active
                        ? channelIds.filter((id) => id !== channel.id)
                        : [...channelIds, channel.id],
                    )
                  }}
                  aria-pressed={active}
                >
                  {channel.title}
                </Button>
              )
            })}
          </div>
        </fieldset>

        {collectionOptions.length ? (
          <fieldset>
            <legend className="text-xs font-semibold uppercase text-foreground/70">
              {t('filters.collections')}
            </legend>
            <div className="flex flex-wrap gap-2">
              {collectionOptions.map((collection) => {
                const active = collectionIds.includes(collection.id)
                return (
                  <Button
                    key={collection.id}
                    variant={active ? 'secondary' : 'outline'}
                    size="sm"
                    onClick={() => {
                      setFiltersTouched(true)
                      setCollectionIds(
                        active
                          ? collectionIds.filter((id) => id !== collection.id)
                          : [...collectionIds, collection.id],
                      )
                    }}
                    aria-pressed={active}
                  >
                    {collection.name}
                  </Button>
                )
              })}
            </div>
          </fieldset>
        ) : null}
      </CardContent>
    </Card>
  )
}
