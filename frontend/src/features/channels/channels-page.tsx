import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { AddChannelDialog } from '@/components/channels/add-channel-dialog'
import { ChannelList } from '@/components/channels/channel-list'
import { EmptyState } from '@/components/common/empty-state'
import { channelsApi, collectionsApi } from '@/lib/api/client'
import { useTranslation } from 'react-i18next'

export function ChannelsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { t } = useTranslation()

  // Handle dialog state from URL param (for navigation from dashboard)
  const addDialogOpen = searchParams.get('add') === 'true'
  const handleDialogOpenChange = (open: boolean) => {
    if (open) {
      setSearchParams({ add: 'true' })
    } else {
      searchParams.delete('add')
      setSearchParams(searchParams)
    }
  }

  const channelsQuery = useQuery({
    queryKey: ['channels'],
    queryFn: async () => (await channelsApi.list()).data,
    refetchInterval: (data) => {
      const channels = Array.isArray(data) ? data : []
      const hasActiveJob = channels.some(
        (channel) =>
          channel.fetch_job?.status === 'queued' || channel.fetch_job?.status === 'running',
      )
      return hasActiveJob ? 3000 : false
    },
  })
  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })

  const addChannel = useMutation({
    mutationFn: (username: string) => channelsApi.add(username),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
    },
  })

  const deleteChannel = useMutation({
    mutationFn: (id: string) => channelsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['channels'] }),
  })

  const channels = Array.isArray(channelsQuery.data) ? channelsQuery.data : []

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-foreground/60">
            {t('channels.subtitle', { count: channels.length })}
          </p>
          <h2 className="text-2xl font-semibold">{t('channels.title')}</h2>
        </div>
        <AddChannelDialog
          onSubmit={(username) => addChannel.mutateAsync(username)}
          open={addDialogOpen}
          onOpenChange={handleDialogOpenChange}
        />
      </div>
      {channels.length === 0 && !channelsQuery.isLoading ? (
        <EmptyState
          title={t('channels.emptyTitle')}
          description={t('channels.emptyDescription')}
        />
      ) : (
        <ChannelList
          channels={channels}
          collections={collectionsQuery.data ?? []}
          onView={(id) => navigate(`/channels/${id}`)}
          onDelete={(id) => deleteChannel.mutate(id)}
        />
      )}
    </div>
  )
}
