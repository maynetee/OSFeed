import { ChannelCard } from '@/components/channels/channel-card'
import type { Channel } from '@/lib/api/client'

interface ChannelListProps {
  channels: Channel[]
  onView?: (id: string) => void
  onFetch?: (id: string, days: number) => void
  onDelete?: (id: string) => void
}

export function ChannelList({ channels, onView, onFetch, onDelete }: ChannelListProps) {
  return (
    <div className="space-y-4">
      {channels.map((channel) => (
        <ChannelCard
          key={channel.id}
          channel={channel}
          onView={onView}
          onFetch={onFetch}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}
