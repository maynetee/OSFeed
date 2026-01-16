import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { LanguageBadge } from '@/components/common/language-badge'
import { Timestamp } from '@/components/common/timestamp'
import type { Channel } from '@/lib/api/client'

interface ChannelCardProps {
  channel: Channel
  onView?: (id: string) => void
  onFetch?: (id: string, days: number) => void
  onDelete?: (id: string) => void
}

export function ChannelCard({ channel, onView, onFetch, onDelete }: ChannelCardProps) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold">{channel.username}</p>
            <p className="text-xs text-foreground/60">
              {channel.title} · {channel.subscriber_count.toLocaleString()} abonnes
            </p>
          </div>
          <LanguageBadge code={channel.detected_language} />
        </div>
        <p className="text-xs text-foreground/60">
          Derniere collecte: {channel.last_fetched_at ? <Timestamp value={channel.last_fetched_at} /> : 'jamais'}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => onView?.(channel.id)}>
            Voir messages
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onFetch?.(channel.id, 7)}>
            Historique 7j
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onFetch?.(channel.id, 30)}>
            Historique 30j
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onDelete?.(channel.id)}>
            Supprimer
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
