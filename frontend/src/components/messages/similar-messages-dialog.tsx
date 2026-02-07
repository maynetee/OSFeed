import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, CheckCircle2, ExternalLink, Info } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Timestamp } from '@/components/common/timestamp'
import { messagesApi } from '@/lib/api/client'
import { analysisApi } from '@/lib/api/analysis'

interface SimilarMessagesDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  messageId: string
}

export function SimilarMessagesDialog({
  open,
  onOpenChange,
  messageId,
}: SimilarMessagesDialogProps) {
  const { t } = useTranslation()

  const similarQuery = useQuery({
    queryKey: ['similar-messages', messageId],
    queryFn: async () => (await messagesApi.getSimilar(messageId)).data,
    enabled: open,
  })

  const messages = similarQuery.data?.messages ?? []

  // Sort by published_at to find earliest (original)
  const sorted = [...messages].sort(
    (a, b) => new Date(a.published_at).getTime() - new Date(b.published_at).getTime()
  )
  const earliestId = sorted.length > 0 ? sorted[0].id : null

  // Extract duplicate_group_id from any message in the group
  const duplicateGroupId = messages.find((m) => m.duplicate_group_id)?.duplicate_group_id

  const correlationQuery = useQuery({
    queryKey: ['correlation', duplicateGroupId],
    queryFn: async () => {
      try {
        return (await analysisApi.getCorrelation(duplicateGroupId!)).data
      } catch (e: unknown) {
        if (e && typeof e === 'object' && 'response' in e) {
          const err = e as { response?: { status?: number } }
          if (err.response?.status === 404) return null
        }
        throw e
      }
    },
    enabled: open && !!duplicateGroupId,
  })

  const correlation = correlationQuery.data

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] overflow-y-auto max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {t('messages.similarTitle')}
            {messages.length > 0 && (
              <Badge variant="muted" className="ml-2">
                {t('messages.sources', { count: messages.length + 1 })}
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        {/* Cross-Source Correlation Analysis */}
        {correlation && (
          <div className="mt-2 space-y-3">
            <h3 className="text-sm font-semibold">{t('analysis.correlation.title')}</h3>

            {correlation.consistent_facts.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-green-500">{t('analysis.correlation.consistentFacts')}</p>
                <ul className="space-y-1">
                  {correlation.consistent_facts.map((fact, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-foreground/80">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-green-500" />
                      {fact}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {correlation.unique_details.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-blue-500">{t('analysis.correlation.uniqueDetails')}</p>
                <ul className="space-y-1">
                  {correlation.unique_details.map((detail, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-foreground/80">
                      <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-blue-500" />
                      {detail}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {correlation.contradictions.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-red-500">{t('analysis.correlation.contradictions')}</p>
                <ul className="space-y-1">
                  {correlation.contradictions.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-foreground/80">
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-500" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {correlation.analysis_text && (
              <p className="text-xs text-foreground/60 italic">{correlation.analysis_text}</p>
            )}
          </div>
        )}

        <div className="mt-4">
          {similarQuery.isLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="h-24 animate-pulse rounded-xl border border-border bg-muted/40"
                />
              ))}
            </div>
          ) : messages.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm text-foreground/60">
                {t('messages.similarEmpty')}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {sorted.map((message) => {
                const isOriginal = message.id === earliestId
                const telegramLink = message.channel_username
                  ? `https://t.me/${message.channel_username}/${message.telegram_message_id}`
                  : null

                return (
                  <Card key={message.id} className={isOriginal ? 'border-green-500/50 bg-green-500/5' : ''}>
                    <CardContent className="py-4">
                      <div className="flex items-center gap-2 text-xs text-foreground/60">
                        <span className="font-semibold text-foreground">
                          {message.channel_title || message.channel_username || message.channel_id}
                        </span>
                        {message.channel_username && (
                          <span className="text-foreground/50">@{message.channel_username}</span>
                        )}
                        {telegramLink && (
                          <a href={telegramLink} target="_blank" rel="noreferrer" className="hover:text-foreground">
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                        <Timestamp value={message.published_at} />
                        {isOriginal && (
                          <Badge variant="success" className="text-[10px]">
                            {t('messages.originalSource')}
                          </Badge>
                        )}
                      </div>
                      <p className="mt-2 text-sm text-foreground/80 line-clamp-3">
                        {message.translated_text ?? message.original_text}
                      </p>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
