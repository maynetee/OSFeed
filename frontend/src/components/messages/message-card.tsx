import { memo, useCallback, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ExternalLink, MessageSquareText } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { DuplicateBadge } from '@/components/messages/duplicate-badge'
import { TelegramEmbed } from '@/components/messages/telegram-embed'
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

export const MessageCard = memo(function MessageCard({ message, onCopy, onExport }: MessageCardProps) {
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

  const channelLabel = message.channel_title || message.channel_username || message.channel_id
  const channelHandle = message.channel_username ? `@${message.channel_username}` : null
  const telegramLink = message.channel_username
    ? `https://t.me/${message.channel_username}/${message.telegram_message_id}`
    : null

  const showTelegramEmbed =
    message.channel_username &&
    message.telegram_message_id &&
    (message.media_type === 'photo' || message.media_type === 'video')

  const similarQuery = useQuery({
    queryKey: ['messages', message.id, 'similar'],
    queryFn: async () => (await messagesApi.similar(message.id, { top_k: 5 })).data,
    enabled: similarOpen,
  })

  const handleOpenSimilar = useCallback(() => setSimilarOpen(true), [])
  const handleCopy = useCallback(() => onCopy?.(message), [onCopy, message])
  const handleExport = useCallback(() => onExport?.(message), [onExport, message])

  return (
    <Card className="animate-rise-in transition hover:border-primary/40">
      <CardContent className="flex flex-col gap-4 py-6">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-foreground/60">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-foreground">{channelLabel}</span>
            {channelHandle ? <span className="text-foreground/50">{channelHandle}</span> : null}
            {telegramLink ? (
              <Button
                asChild
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-foreground/60 hover:text-foreground"
              >
                <a href={telegramLink} target="_blank" rel="noreferrer" aria-label={t('messages.openTelegram')}>
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </Button>
            ) : null}
            <Timestamp value={message.published_at} />
            {message.source_language ? <Badge variant="muted">{message.source_language}</Badge> : null}
            {message.needs_translation && !message.translated_text ? (
              <Badge variant="outline" className="animate-pulse">
                {t('messages.translating')}
              </Badge>
            ) : null}
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

        {showTelegramEmbed ? (
          <TelegramEmbed
            channelUsername={message.channel_username!}
            messageId={message.telegram_message_id!}
          />
        ) : null}

        {message.entities ? (
          <div className="grid gap-3 md:grid-cols-3">
            <EntityTags label={t('messages.entitiesPeople')} entities={message.entities.persons} />
            <EntityTags label={t('messages.entitiesLocations')} entities={message.entities.locations} />
            <EntityTags label={t('messages.entitiesOrganizations')} entities={message.entities.organizations} />
          </div>
        ) : null}

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleOpenSimilar}>
            {t('messages.similar')}
          </Button>
          <Button variant="ghost" size="sm" onClick={handleCopy}>
            {t('messages.copy')}
          </Button>
          <Button variant="ghost" size="sm" onClick={handleExport}>
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
                        <span className="font-semibold text-foreground">
                          {similarMessage.channel_title ||
                            similarMessage.channel_username ||
                            similarMessage.channel_id}
                        </span>
                        {similarMessage.channel_username ? (
                          <span className="text-foreground/50">
                            @{similarMessage.channel_username}
                          </span>
                        ) : null}
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
})
