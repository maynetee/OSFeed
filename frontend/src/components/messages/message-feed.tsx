import { memo, useRef, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useVirtualizer } from '@tanstack/react-virtual'

import { MessageCard } from '@/components/messages/message-card'
import { MessageSkeleton } from '@/components/messages/message-skeleton'
import { EmptyState } from '@/components/common/empty-state'
import { useLazyTranslation } from '@/hooks/use-lazy-translation'
import type { Message } from '@/lib/api/client'

interface MessageFeedProps {
  messages: Message[]
  isLoading?: boolean
  isFetchingNextPage?: boolean
  onCopy?: (message: Message) => void
  onExport?: (message: Message) => void
  onEndReached?: () => void
}

export const MessageFeed = memo(function MessageFeed({
  messages,
  isLoading,
  isFetchingNextPage,
  onCopy,
  onExport,
  onEndReached,
}: MessageFeedProps) {
  const { t } = useTranslation()
  const parentRef = useRef<HTMLDivElement>(null)

  // Trigger lazy translation for visible messages that need it
  useLazyTranslation({
    messages,
    enabled: !isLoading,
  })

  // Virtualizer instance
  const rowVirtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 180, // Approximate height of a message card
    overscan: 5,
  })

  const virtualItems = rowVirtualizer.getVirtualItems()

  // Infinite scroll logic using virtualizer
  const handleScroll = useCallback(() => {
    if (!parentRef.current || !onEndReached || isFetchingNextPage || isLoading) return

    const { scrollTop, scrollHeight, clientHeight } = parentRef.current
    // Trigger when within 300px of bottom
    if (scrollHeight - scrollTop - clientHeight < 300) {
      onEndReached()
    }
  }, [onEndReached, isFetchingNextPage, isLoading])

  // Attach scroll listener manually to ensure it fires reliably with virtualization
  useEffect(() => {
    const element = parentRef.current
    if (!element) return

    element.addEventListener('scroll', handleScroll)
    return () => element.removeEventListener('scroll', handleScroll)
  }, [handleScroll])

  if (!isLoading && messages.length === 0) {
    return (
      <EmptyState
        title={t('messages.noMessagesTitle')}
        description={t('messages.noMessagesDescription')}
      />
    )
  }

  return (
    <div
      ref={parentRef}
      className="h-[70vh] overflow-y-auto rounded-2xl border border-border/60 bg-background/60 p-4 space-y-4"
      role="feed"
      aria-busy={Boolean(isLoading || isFetchingNextPage)}
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualItem) => {
          const message = messages[virtualItem.index]
          return (
            <div
              key={message.id}
              data-index={virtualItem.index}
              ref={rowVirtualizer.measureElement}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`,
                paddingBottom: '16px', // Matches space-y-4 gap
              }}
            >
              <MessageCard message={message} onCopy={onCopy} onExport={onExport} />
            </div>
          )
        })}
      </div>

      {/* Loading states below the virtualized list */}
      {isLoading && messages.length === 0 && (
        <div className="space-y-4 mt-4">
          <MessageSkeleton count={3} />
        </div>
      )}

      {isFetchingNextPage && (
        <div className="py-4 text-center text-xs text-foreground/50">
          {t('messages.loadingMore')}
        </div>
      )}
    </div>
  )
})
