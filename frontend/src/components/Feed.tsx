import { useState, useRef, useCallback, useEffect, useMemo } from 'react'
import { useQuery, useInfiniteQuery } from '@tanstack/react-query'
import { messagesApi, channelsApi, Channel } from '../api/client'

export default function Feed() {
  const [selectedChannel, setSelectedChannel] = useState<string | undefined>()
  const loadMoreRef = useRef<HTMLDivElement>(null)

  const { data: channels } = useQuery({
    queryKey: ['channels'],
    queryFn: () => channelsApi.list().then((res) => res.data),
  })

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ['messages', { channel_id: selectedChannel }],
    queryFn: async ({ pageParam = 0 }) => {
      const res = await messagesApi.list({
        channel_id: selectedChannel,
        limit: 20,
        offset: pageParam,
      })
      return res.data
    },
    getNextPageParam: (lastPage, allPages) => {
      const loadedCount = allPages.reduce((acc, page) => acc + page.messages.length, 0)
      if (loadedCount < lastPage.total) {
        return loadedCount
      }
      return undefined
    },
    initialPageParam: 0,
  })

  // Infinite scroll observer
  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries
      if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) {
        fetchNextPage()
      }
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage]
  )

  useEffect(() => {
    const element = loadMoreRef.current
    if (!element) return

    const observer = new IntersectionObserver(handleObserver, {
      root: null,
      rootMargin: '100px',
      threshold: 0,
    })

    observer.observe(element)
    return () => observer.disconnect()
  }, [handleObserver])

  const allMessages = data?.pages.flatMap((page) => page.messages) || []
  const totalCount = data?.pages[0]?.total || 0

  // Create a Map for O(1) channel lookup instead of O(n) find() per message
  const channelsMap = useMemo(() => {
    const map = new Map<string, Channel>()
    channels?.forEach((channel) => map.set(channel.id, channel))
    return map
  }, [channels])

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Message Feed</h2>
        <span className="text-gray-500">{totalCount} messages total</span>
      </div>

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Filter by Channel:</label>
          <select
            value={selectedChannel || ''}
            onChange={(e) => {
              setSelectedChannel(e.target.value || undefined)
            }}
            className="mt-1 block w-64 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
          >
            <option value="">All Channels</option>
            {channels?.map((channel) => (
              <option key={channel.id} value={channel.id}>
                {channel.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading messages...</div>
          </div>
        ) : allMessages.length > 0 ? (
          <>
            {allMessages.map((message) => {
              const channel = channelsMap.get(message.channel_id)

              return (
                <div key={message.id} className="bg-white shadow rounded-lg p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {channel?.title || 'Unknown Channel'}
                        </span>
                        {message.is_duplicate && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Duplicate
                          </span>
                        )}
                        {message.source_language && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {message.source_language.toUpperCase()}
                          </span>
                        )}
                      </div>

                      <div className="text-gray-900 mb-3 whitespace-pre-wrap">
                        {message.translated_text || message.original_text}
                      </div>

                      {message.translated_text && message.original_text !== message.translated_text && (
                        <details className="mt-2">
                          <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                            Show original
                          </summary>
                          <div className="mt-2 text-sm text-gray-600 bg-gray-50 p-3 rounded whitespace-pre-wrap">
                            {message.original_text}
                          </div>
                        </details>
                      )}
                    </div>

                    <div className="ml-4 text-sm text-gray-500 text-right whitespace-nowrap">
                      {new Date(message.published_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              )
            })}

            {/* Load more trigger */}
            <div ref={loadMoreRef} className="py-4">
              {isFetchingNextPage ? (
                <div className="text-center text-gray-500">Loading more...</div>
              ) : hasNextPage ? (
                <div className="text-center text-gray-400">Scroll for more</div>
              ) : (
                <div className="text-center text-gray-400">No more messages</div>
              )}
            </div>
          </>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <div className="text-gray-500">
              No messages found. Add some channels to get started.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
