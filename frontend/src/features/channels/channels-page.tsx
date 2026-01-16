import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { AddChannelDialog } from '@/components/channels/add-channel-dialog'
import { ChannelList } from '@/components/channels/channel-list'
import { EmptyState } from '@/components/common/empty-state'
import { channelsApi, messagesApi } from '@/lib/api/client'

export function ChannelsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const channelsQuery = useQuery({
    queryKey: ['channels'],
    queryFn: async () => (await channelsApi.list()).data,
  })

  const addChannel = useMutation({
    mutationFn: (username: string) => channelsApi.add(username),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['channels'] }),
  })

  const deleteChannel = useMutation({
    mutationFn: (id: string) => channelsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['channels'] }),
  })

  const fetchHistorical = useMutation({
    mutationFn: ({ id, days }: { id: string; days: number }) =>
      messagesApi.fetchHistorical(id, days),
  })

  const channels = channelsQuery.data ?? []

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-foreground/60">{channels.length} canaux actifs</p>
          <h2 className="text-2xl font-semibold">Sources Telegram</h2>
        </div>
        <AddChannelDialog onSubmit={(username) => addChannel.mutateAsync(username)} />
      </div>
      {channels.length === 0 && !channelsQuery.isLoading ? (
        <EmptyState
          title="Aucun canal"
          description="Ajoutez une source Telegram pour commencer la veille."
        />
      ) : (
        <ChannelList
          channels={channels}
          onView={(id) => navigate(`/channels/${id}`)}
          onFetch={(id, days) => fetchHistorical.mutate({ id, days })}
          onDelete={(id) => deleteChannel.mutate(id)}
        />
      )}
    </div>
  )
}
