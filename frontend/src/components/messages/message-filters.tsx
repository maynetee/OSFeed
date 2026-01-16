import { useMemo } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useFilterStore } from '@/stores/filter-store'

interface MessageFiltersProps {
  channels: { id: string; title: string }[]
}

export function MessageFilters({ channels }: MessageFiltersProps) {
  const channelIds = useFilterStore((state) => state.channelIds)
  const dateRange = useFilterStore((state) => state.dateRange)
  const setChannelIds = useFilterStore((state) => state.setChannelIds)
  const setDateRange = useFilterStore((state) => state.setDateRange)

  const channelOptions = useMemo(
    () => channels.map((channel) => ({ id: channel.id, title: channel.title })),
    [channels],
  )

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 py-6">
        <div>
          <p className="text-sm font-semibold">Filtres</p>
          <p className="text-xs text-foreground/60">Affinez le flux en temps reel.</p>
        </div>

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
      </CardContent>
    </Card>
  )
}
