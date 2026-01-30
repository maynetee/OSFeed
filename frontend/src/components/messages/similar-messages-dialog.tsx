import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { MessageCard } from '@/components/messages/message-card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { messagesApi } from '@/lib/api/client'

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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] overflow-y-auto max-w-3xl">
        <DialogHeader>
          <DialogTitle>{t('messages.similarTitle')}</DialogTitle>
        </DialogHeader>

        <div className="mt-4">
          {similarQuery.isLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="h-32 animate-pulse rounded-2xl border border-border bg-muted/40"
                />
              ))}
            </div>
          ) : similarQuery.data?.messages.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm text-foreground/60">
                {t('messages.similarEmpty')}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {similarQuery.data?.messages.map((message) => (
                <MessageCard key={message.id} message={message} />
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
