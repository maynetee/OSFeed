import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { channelsApi, messagesApi } from '@/lib/api/client'
import { MessageFeed } from '@/components/messages/message-feed'
import { Card, CardContent } from '@/components/ui/card'

export function ChannelDetailPage() {
  const { id } = useParams()

  const channelQuery = useQuery({
    queryKey: ['channels', id],
    queryFn: async () => (await channelsApi.list()).data.find((channel) => channel.id === id),
    enabled: Boolean(id),
  })

  const messagesQuery = useQuery({
    queryKey: ['channel-messages', id],
    queryFn: async () => (await messagesApi.list({ channel_id: id, limit: 20, offset: 0 })).data,
    enabled: Boolean(id),
  })

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardContent className="py-6">
          <div className="flex flex-col gap-2">
            <p className="text-sm text-foreground/60">Canal</p>
            <h2 className="text-2xl font-semibold">
              {channelQuery.data?.title ?? 'Chargement...'}
            </h2>
            <p className="text-sm text-foreground/60">{channelQuery.data?.username}</p>
          </div>
        </CardContent>
      </Card>

      <MessageFeed
        messages={messagesQuery.data?.messages ?? []}
        isLoading={messagesQuery.isLoading}
      />
    </div>
  )
}
