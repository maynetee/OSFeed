import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MessageSquareText } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { DuplicateBadge } from '@/components/messages/duplicate-badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Timestamp } from '@/components/common/timestamp'
import { EntityTags } from '@/components/digests/entity-tags'
import { messagesApi } from '@/lib/api/client'
import type { Message } from '@/lib/api/client'

interface MessageCardProps {
  message: Message
  onCopy?: (message: Message) => void
  onExport?: (message: Message) => void
}

export function MessageCard({ message, onCopy, onExport }: MessageCardProps) {
  const { t } = useTranslation()
  const [similarOpen, setSimilarOpen] = useState(false)
  const similarityScore = message.similarity_score
  const duplicateScore = useMemo(() => {
    if (typeof message.originality_score !== 'number') return null
    return Math.max(0, Math.min(100, 100 - message.originality_score))
  }, [message.originality_score])

  const showPrimarySource =
    !message.is_duplicate && (message.originality_score ?? 100) >= 90
  const showPropaganda =
    message.is_duplicate && typeof duplicateScore === 'number' && duplicateScore >= 80

  const similarQuery = useQuery({
    queryKey: ['messages', message.id, 'similar'],
    queryFn: async () => (await messagesApi.similar(message.id, { top_k: 5 })).data,
    enabled: similarOpen,
  })

  return (
    <Card className="animate-rise-in transition hover:border-primary/40">
      <CardContent className="flex flex-col gap-4 py-6">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-foreground/60">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-foreground">{message.channel_id}</span>
            <Timestamp value={message.published_at} />
            {message.source_language ? <Badge variant="muted">{message.source_language}</Badge> : null}
            {message.translated_text ? <Badge variant="success">{t('messages.translated')}</Badge> : null}
          </div>
          <div className="flex items-center gap-2">
            <DuplicateBadge isDuplicate={message.is_duplicate} score={duplicateScore} />
            {showPrimarySource ? <Badge variant="success">{t('messages.primarySource')}</Badge> : null}
            {showPropaganda ? <Badge variant="danger">{t('messages.propaganda')}</Badge> : null}
            {typeof similarityScore === 'number' ? (
              <Badge variant="outline">
                {t('messages.similarity')} {Math.round(similarityScore * 100)}%
              </Badge>
            ) : null}
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
                {t('messages.original')}
              </p>
              <p className="mt-2 text-foreground/70">{message.original_text}</p>
            </div>
          ) : null}
        </div>

        {message.entities ? (
          <div className="grid gap-3 md:grid-cols-3">
            <EntityTags label={t('messages.entitiesPeople')} entities={message.entities.persons} />
            <EntityTags label={t('messages.entitiesLocations')} entities={message.entities.locations} />
            <EntityTags label={t('messages.entitiesOrganizations')} entities={message.entities.organizations} />
          </div>
        ) : null}

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setSimilarOpen(true)}>
            {t('messages.similar')}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onCopy?.(message)}>
            {t('messages.copy')}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onExport?.(message)}>
            {t('messages.export')}
          </Button>
        </div>
      </CardContent>

      <Dialog open={similarOpen} onOpenChange={setSimilarOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{t('messages.similarTitle')}</DialogTitle>
          </DialogHeader>
          {similarQuery.isLoading ? (
            <p className="text-sm text-foreground/60">{t('messages.similarLoading')}</p>
          ) : similarQuery.data?.messages.length ? (
            <div className="space-y-3">
              {similarQuery.data.messages.map((similarMessage) => (
                <Card key={similarMessage.id} className="border-border/60">
                  <CardContent className="py-4">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-foreground/60">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-foreground">{similarMessage.channel_id}</span>
                        <Timestamp value={similarMessage.published_at} />
                      </div>
                      {typeof similarMessage.similarity_score === 'number' ? (
                        <Badge variant="outline">
                          {t('messages.similarity')} {Math.round(similarMessage.similarity_score * 100)}%
                        </Badge>
                      ) : null}
                    </div>
                    <p className="mt-2 text-sm text-foreground/80">
                      {similarMessage.translated_text ?? similarMessage.original_text}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <p className="text-sm text-foreground/60">{t('messages.similarEmpty')}</p>
          )}
        </DialogContent>
      </Dialog>
    </Card>
  )
}
