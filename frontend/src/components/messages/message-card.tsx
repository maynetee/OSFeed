import { lazy, memo, Suspense, useCallback, useMemo, useState } from 'react'
import { AlertTriangle, ExternalLink, Image, MessageSquareText } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'

import { useMutation, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DuplicateBadge } from '@/components/messages/duplicate-badge'
import { MediaPreview } from '@/components/messages/telegram-embed'
import { Timestamp } from '@/components/common/timestamp'
import type { Message } from '@/lib/api/client'
import { messagesApi } from '@/lib/api/client'

const SimilarMessagesDialog = lazy(() =>
  import('./similar-messages-dialog').then((m) => ({ default: m.SimilarMessagesDialog })),
)

interface MessageCardProps {
  message: Message
  onCopy?: (message: Message) => void
  onExport?: (message: Message) => void
}

export const MessageCard = memo(function MessageCard({
  message,
  onCopy,
  onExport,
}: MessageCardProps) {
  const { t } = useTranslation()
  const [showMedia, setShowMedia] = useState(false)
  const [showSimilar, setShowSimilar] = useState(false)
  const queryClient = useQueryClient()
  const translateMutation = useMutation({
    mutationFn: () => messagesApi.translateById(message.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
  })

  const duplicateScore = useMemo(() => {
    if (typeof message.originality_score !== 'number') return null
    return Math.max(0, Math.min(100, 100 - message.originality_score))
  }, [message.originality_score])

  const showPrimarySource = !message.is_duplicate && (message.originality_score ?? 100) >= 90
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

  const handleCopy = useCallback(() => onCopy?.(message), [onCopy, message])
  const handleExport = useCallback(() => onExport?.(message), [onExport, message])

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{
        scale: 1.005,
        boxShadow: '0 8px 25px rgba(0, 0, 0, 0.08)',
      }}
      transition={{ duration: 0.2 }}
      className="relative rounded-xl border border-border bg-card text-card-foreground shadow-sm transition hover:border-primary/40 overflow-hidden"
    >
      {/* Channel accent bar */}
      <div className="absolute left-0 top-0 h-full w-1 bg-primary/60" />
      <div className="flex flex-col gap-4 py-6 pl-6 pr-5">
        <div className="flex flex-col gap-2 text-xs sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
          {/* Metadata Group */}
          <div className="flex flex-wrap items-center gap-1.5 text-foreground/60 md:gap-2">
            <span className="text-base font-semibold text-foreground">{channelLabel}</span>
            {channelHandle ? <span className="text-foreground/50">{channelHandle}</span> : null}
            {telegramLink ? (
              <Button
                asChild
                variant="ghost"
                size="icon"
                className="text-foreground/60 hover:text-foreground"
              >
                <a
                  href={telegramLink}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={t('messages.openTelegram')}
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </Button>
            ) : null}
            <Timestamp value={message.published_at} />
          </div>

          {/* Status Badges Group */}
          <div className="flex flex-wrap items-center gap-1.5 md:gap-2 lg:gap-2.5">
            {message.source_language ? (
              <Badge variant="muted">{message.source_language}</Badge>
            ) : null}
            {message.needs_translation && !message.translated_text ? (
              <Badge variant="outline" className="animate-pulse">
                {t('messages.translating')}
              </Badge>
            ) : null}
            {message.translated_text ? (
              <Badge variant="success">{t('messages.translated')}</Badge>
            ) : null}
            {!message.translated_text && !message.needs_translation && message.original_text ? (
              <Button
                variant="ghost"
                size="sm"
                className="h-5 px-2 text-xs"
                onClick={() => translateMutation.mutate()}
                disabled={translateMutation.isPending}
              >
                {translateMutation.isPending ? t('messages.translating') : t('messages.translate')}
              </Button>
            ) : null}
            <DuplicateBadge
              isDuplicate={message.is_duplicate}
              score={duplicateScore}
              duplicateCount={message.duplicate_count}
              onClick={message.duplicate_group_id ? () => setShowSimilar(true) : undefined}
            />
            {showPrimarySource ? (
              <Badge variant="success">{t('messages.primarySource')}</Badge>
            ) : null}
            {showPropaganda ? <Badge variant="danger">{t('messages.propaganda')}</Badge> : null}
            {message.has_correlation ? (
              <Badge variant="outline" className="border-blue-500/50 text-blue-500">
                {t('analysis.correlation.crossReferenced')}
              </Badge>
            ) : null}
            {message.media_type ? <Badge variant="outline">{message.media_type}</Badge> : null}
            {message.escalation_level === 'high' ? (
              <Badge
                variant="danger"
                className="gap-1"
                title={message.escalation_factors?.join(', ')}
              >
                <AlertTriangle className="h-3 w-3" />
                {t('analysis.escalation.high')}
              </Badge>
            ) : message.escalation_level === 'medium' ? (
              <Badge
                variant="outline"
                className="gap-1 border-amber-500/50 text-amber-500"
                title={message.escalation_factors?.join(', ')}
              >
                <AlertTriangle className="h-3 w-3" />
                {t('analysis.escalation.medium')}
              </Badge>
            ) : null}
            {message.pattern_ids && message.pattern_ids.length > 0 ? (
              <Badge variant="outline" className="border-purple-500/50 text-purple-500">
                {t('analysis.patterns.partOfPattern')}
              </Badge>
            ) : null}
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

        {message.escalation_level &&
        message.escalation_level !== 'low' &&
        message.escalation_factors &&
        message.escalation_factors.length > 0 ? (
          <div
            className={`rounded-lg border p-2 text-xs ${message.escalation_level === 'high' ? 'border-red-500/30 bg-red-500/5 text-red-400' : 'border-amber-500/30 bg-amber-500/5 text-amber-400'}`}
          >
            <p className="font-medium mb-1">{t('analysis.escalation.factors')}:</p>
            <ul className="list-disc list-inside space-y-0.5">
              {message.escalation_factors.map((factor, i) => (
                <li key={i}>{factor}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {showTelegramEmbed && !showMedia ? (
          <Button variant="outline" size="lg" onClick={() => setShowMedia(true)} className="w-fit">
            <Image className="mr-1.5 h-3.5 w-3.5" />
            {t('messages.showMedia')}
          </Button>
        ) : null}

        {showTelegramEmbed && showMedia ? (
          <MediaPreview
            messageId={message.id}
            mediaType={message.media_type as 'photo' | 'video'}
            channelUsername={message.channel_username!}
            telegramMessageId={message.telegram_message_id!}
          />
        ) : null}

        <div className="flex flex-wrap items-center gap-2">
          {message.duplicate_group_id ? (
            <Button variant="ghost" size="lg" onClick={() => setShowSimilar(true)}>
              {t('messages.similar')}
            </Button>
          ) : null}
          <Button variant="ghost" size="lg" onClick={handleCopy}>
            {t('messages.copy')}
          </Button>
          <Button variant="ghost" size="lg" onClick={handleExport}>
            {t('messages.export')}
          </Button>
        </div>

        {showSimilar && (
          <Suspense fallback={null}>
            <SimilarMessagesDialog
              open={showSimilar}
              onOpenChange={setShowSimilar}
              messageId={message.id}
            />
          </Suspense>
        )}
      </div>
    </motion.div>
  )
})
