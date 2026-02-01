import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { LanguageBadge } from '@/components/common/language-badge'
import { Timestamp } from '@/components/common/timestamp'
import { Badge } from '@/components/ui/badge'
import type { Channel } from '@/lib/api/client'
import { useTranslation } from 'react-i18next'
import type { Collection } from '@/lib/api/client'
import { ChannelCollectionPicker } from '@/components/channels/channel-collection-picker'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

interface ChannelCardProps {
  channel: Channel
  collections?: Collection[]
  onView?: (id: string) => void
  onDelete?: (id: string) => void
}

export function ChannelCard({
  channel,
  collections = [],
  onView,
  onDelete,
}: ChannelCardProps) {
  const { t } = useTranslation()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const channelCollections = collections.filter((collection) =>
    collection.channel_ids.includes(channel.id),
  )
  const fetchJob = channel.fetch_job
  const statusLabels: Record<string, string> = {
    queued: t('channels.fetchQueued'),
    running: t('channels.fetchRunning'),
    completed: t('channels.fetchCompleted'),
    failed: t('channels.fetchFailed'),
  }
  const stageLabels: Record<string, string> = {
    info: t('channels.fetchStageInfo'),
    fetching: t('channels.fetchStageFetching'),
    checking: t('channels.fetchStageChecking'),
    translating: t('channels.fetchStageTranslating'),
    saving: t('channels.fetchStageSaving'),
  }
  const statusLabel = fetchJob?.status ? statusLabels[fetchJob.status] ?? fetchJob.status : null
  const stageLabel = fetchJob?.stage ? stageLabels[fetchJob.stage] ?? fetchJob.stage : null
  const countParts = []
  if (fetchJob?.new_messages !== undefined && fetchJob?.new_messages !== null) {
    countParts.push(t('channels.fetchNew', { count: fetchJob.new_messages }))
  }
  if (fetchJob?.total_messages !== undefined && fetchJob?.total_messages !== null) {
    countParts.push(t('channels.fetchTotal', { count: fetchJob.total_messages }))
  }
  const progressLabel =
    fetchJob?.processed_messages !== undefined &&
      fetchJob?.processed_messages !== null &&
      fetchJob?.new_messages !== undefined &&
      fetchJob?.new_messages !== null &&
      fetchJob.new_messages > 0
      ? t('channels.fetchProgress', { done: fetchJob.processed_messages, total: fetchJob.new_messages })
      : null

  return (
    <Card className="animate-rise-in">
      <CardContent className="flex flex-col gap-3 py-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold">{channel.username}</p>
            <p className="text-xs text-foreground/60">
              {t('channels.subscribers', { count: channel.subscriber_count })}
            </p>
          </div>
          <LanguageBadge code={channel.detected_language} />
        </div>
        <p className="text-xs text-foreground/60">
          {t('channels.lastFetched')}{' '}
          {channel.last_fetched_at ? <Timestamp value={channel.last_fetched_at} /> : t('channels.never')}
        </p>
        {fetchJob && statusLabel ? (
          <p className="text-xs text-foreground/60">
            {t('channels.fetchStatus')} {statusLabel}
            {fetchJob.days ? ` · ${fetchJob.days}d` : ''}
            {stageLabel ? ` · ${stageLabel}` : ''}
            {countParts.length ? ` · ${countParts.join(' · ')}` : ''}
            {progressLabel ? ` · ${progressLabel}` : ''}
          </p>
        ) : null}
        {channelCollections.length ? (
          <div className="flex flex-wrap gap-2">
            {channelCollections.map((collection) => (
              <Badge key={collection.id} variant="outline">
                {collection.name}
              </Badge>
            ))}
          </div>
        ) : null}
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="lg" onClick={() => onView?.(channel.id)}>
            {t('channels.viewMessages')}
          </Button>
          <ChannelCollectionPicker channelId={channel.id} collections={collections} />
          <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="lg">
                {t('channels.delete')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('channels.deleteConfirmTitle')}</DialogTitle>
                <DialogDescription>
                  {t('channels.deleteConfirmMessage', { username: channel.username })}
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                  {t('common.cancel')}
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => {
                    onDelete?.(channel.id)
                    setDeleteDialogOpen(false)
                  }}
                >
                  {t('channels.delete')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardContent>
    </Card>
  )
}
