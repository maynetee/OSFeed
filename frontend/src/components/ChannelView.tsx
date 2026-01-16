import { useParams, Link } from 'react-router-dom'
import { useQuery, useInfiniteQuery, useMutation } from '@tanstack/react-query'
import { channelsApi, messagesApi } from '../api/client'
import { useEffect, useRef, useCallback } from 'react'

export default function ChannelView() {
  const { channelId } = useParams<{ channelId: string }>()
  const loadMoreRef = useRef<HTMLDivElement>(null)

  const { data: channels } = useQuery({
    queryKey: ['channels'],
    queryFn: () => channelsApi.list().then((res) => res.data),
  })

  const channel = channels?.find((c) => c.id === channelId)

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ['channel-messages', channelId],
    queryFn: async ({ pageParam = 0 }) => {
      const res = await messagesApi.list({
        channel_id: channelId,
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

  const fetchHistoricalMutation = useMutation({
    mutationFn: (days: number) => messagesApi.fetchHistorical(channelId || '', days),
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <Link to="/channels" className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block">
            &larr; Back to Channels
          </Link>
          <h2 className="text-3xl font-bold text-gray-900">{channel?.title || 'Channel'}</h2>
          <p className="text-gray-500">@{channel?.username}</p>
          {channel?.description && (
            <p className="text-gray-600 mt-2 text-sm">{channel.description}</p>
          )}
        </div>

        <div className="flex space-x-2">
          <button
            onClick={() => fetchHistoricalMutation.mutate(7)}
            disabled={fetchHistoricalMutation.isPending}
            className="px-4 py-2 border border-blue-600 text-blue-600 text-sm font-medium rounded-md hover:bg-blue-50 disabled:opacity-50"
          >
            {fetchHistoricalMutation.isPending ? 'Loading...' : 'Load 7 days'}
          </button>
          <button
            onClick={() => fetchHistoricalMutation.mutate(30)}
            disabled={fetchHistoricalMutation.isPending}
            className="px-4 py-2 border border-blue-600 text-blue-600 text-sm font-medium rounded-md hover:bg-blue-50 disabled:opacity-50"
          >
            {fetchHistoricalMutation.isPending ? 'Loading...' : 'Load 30 days'}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-white shadow rounded-lg p-4 flex items-center justify-between">
        <div>
          <span className="text-2xl font-bold text-blue-600">{totalCount}</span>
          <span className="text-gray-500 ml-2">messages</span>
        </div>
        <div className="text-sm text-gray-500">
          {channel?.subscriber_count?.toLocaleString()} subscribers
        </div>
      </div>

      {fetchHistoricalMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-800">
          Historical messages are being fetched in background. Refresh in a few moments.
        </div>
      )}

      {/* Messages */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading messages...</div>
          </div>
        ) : allMessages.length > 0 ? (
          <>
            {allMessages.map((message) => (
              <div key={message.id} className="bg-white shadow rounded-lg p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      {message.source_language && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {message.source_language.toUpperCase()}
                        </span>
                      )}
                      {message.is_duplicate && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Duplicate
                        </span>
                      )}
                    </div>

                    <div className="text-gray-900 mb-3 whitespace-pre-wrap">
                      {message.translated_text || message.original_text}
                    </div>

                    {message.translated_text &&
                      message.original_text !== message.translated_text && (
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
            ))}

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
            <p className="text-gray-500">No messages yet.</p>
            <button
              onClick={() => fetchHistoricalMutation.mutate(7)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Load historical messages (7 days)
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
