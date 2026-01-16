import { MessageSquareText } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { DuplicateBadge } from '@/components/messages/duplicate-badge'
import { Timestamp } from '@/components/common/timestamp'
import type { Message } from '@/lib/api/client'

interface MessageCardProps {
  message: Message
  onCopy?: (message: Message) => void
  onExport?: (message: Message) => void
}

export function MessageCard({ message, onCopy, onExport }: MessageCardProps) {
  return (
    <Card className="transition hover:border-primary/40">
      <CardContent className="flex flex-col gap-4 py-6">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-foreground/60">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-foreground">{message.channel_id}</span>
            <Timestamp value={message.published_at} />
            {message.source_language ? <Badge variant="muted">{message.source_language}</Badge> : null}
            {message.translated_text ? <Badge variant="success">Traduit</Badge> : null}
          </div>
          <div className="flex items-center gap-2">
            <DuplicateBadge isDuplicate={message.is_duplicate} />
            {message.media_type ? <Badge variant="outline">{message.media_type}</Badge> : null}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm leading-relaxed text-foreground/80">
            {message.translated_text ?? message.original_text}
          </p>
          {message.translated_text ? (
            <div className="rounded-lg border border-border/60 bg-muted/40 p-3 text-xs text-foreground/60">
              <p className="flex items-center gap-2 font-semibold text-foreground/60">
                <MessageSquareText className="h-3.5 w-3.5" />
                Original
              </p>
              <p className="mt-2 text-foreground/70">{message.original_text}</p>
            </div>
          ) : null}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm">Voir similaires</Button>
          <Button variant="ghost" size="sm" onClick={() => onCopy?.(message)}>
            Copier
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onExport?.(message)}>
            Exporter
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
