import { ChannelCard } from '@/components/channels/channel-card'
import type { Channel, Collection } from '@/lib/api/client'

interface ChannelListProps {
  channels: Channel[]
  collections?: Collection[]
  onView?: (id: string) => void
  onDelete?: (id: string) => void
}

export function ChannelList({ channels, collections = [], onView, onDelete }: ChannelListProps) {
  return (
    <div className="space-y-4">
      {channels.map((channel) => (
        <ChannelCard
          key={channel.id}
          channel={channel}
          collections={collections}
          onView={onView}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}
