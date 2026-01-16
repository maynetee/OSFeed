import { useMemo, useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'

import { MessageCard } from '@/components/messages/message-card'
import { EmptyState } from '@/components/common/empty-state'
import type { Message } from '@/lib/api/client'

interface MessageFeedProps {
  messages: Message[]
  isLoading?: boolean
  isFetchingNextPage?: boolean
  onCopy?: (message: Message) => void
  onExport?: (message: Message) => void
  onEndReached?: () => void
}

export function MessageFeed({
  messages,
  isLoading,
  isFetchingNextPage,
  onCopy,
  onExport,
  onEndReached,
}: MessageFeedProps) {
  const parentRef = useRef<HTMLDivElement>(null)

  const rows = useMemo(() => messages, [messages])

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 240,
    overscan: 6,
  })

  if (!isLoading && rows.length === 0) {
    return (
      <EmptyState
        title="Aucun message"
        description="Lancez une recherche ou ajustez les filtres pour afficher le flux."
      />
    )
  }

  return (
    <div
      ref={parentRef}
      className="h-[70vh] overflow-y-auto rounded-2xl border border-border/60 bg-background/60 p-4"
      onScroll={(event) => {
        if (!onEndReached || isFetchingNextPage) return
        const target = event.currentTarget
        const remaining = target.scrollHeight - target.scrollTop - target.clientHeight
        if (remaining < 200) {
          onEndReached()
        }
      }}
    >
      {isLoading && rows.length === 0 ? (
        <div className="py-10 text-sm text-foreground/60">Chargement du flux...</div>
      ) : null}
      <div
        style={{ height: rowVirtualizer.getTotalSize() }}
        className="relative"
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const message = rows[virtualRow.index]
          return (
            <div
              key={message.id}
              className="absolute left-0 top-0 w-full px-1"
              style={{ transform: `translateY(${virtualRow.start}px)` }}
            >
              <div className="pb-4">
                <MessageCard message={message} onCopy={onCopy} onExport={onExport} />
              </div>
            </div>
          )
        })}
      </div>
      {isFetchingNextPage ? (
        <div className="py-4 text-center text-xs text-foreground/50">Chargement...</div>
      ) : null}
    </div>
  )
}
