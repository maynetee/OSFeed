import { useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { summariesApi, channelsApi, messagesApi, statsApi, exportsApi } from '../api/client'

export default function Dashboard() {
  const [isGenerating, setIsGenerating] = useState(false)
  const queryClient = useQueryClient()

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['daily-summary'],
    queryFn: () => summariesApi.getDaily().then((res) => res.data),
  })

  const { data: overview } = useQuery({
    queryKey: ['stats-overview'],
    queryFn: () => statsApi.overview().then((res) => res.data),
  })

  const { data: messagesByDay } = useQuery({
    queryKey: ['stats-messages-by-day'],
    queryFn: () => statsApi.messagesByDay(7).then((res) => res.data),
  })

  const { data: messagesByChannel } = useQuery({
    queryKey: ['stats-messages-by-channel'],
    queryFn: () => statsApi.messagesByChannel(6).then((res) => res.data),
  })

  const { data: channels } = useQuery({
    queryKey: ['channels'],
    queryFn: () => channelsApi.list().then((res) => res.data),
  })

  const { data: messagesData } = useQuery({
    queryKey: ['messages', { limit: 5 }],
    queryFn: () => messagesApi.list({ limit: 5 }).then((res) => res.data),
  })

  const generateSummary = async () => {
    setIsGenerating(true)
    try {
      await summariesApi.generate()
      await queryClient.invalidateQueries({ queryKey: ['daily-summary'] })
    } catch (error) {
      alert('Failed to generate summary')
    } finally {
      setIsGenerating(false)
    }
  }

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }

  const handleExportStats = async () => {
    const response = await statsApi.exportCsv(7)
    downloadBlob(new Blob([response.data]), 'telescope-stats.csv')
  }

  const handleExportMessages = async () => {
    const response = await exportsApi.messagesCsv()
    downloadBlob(new Blob([response.data]), 'telescope-messages.csv')
  }

  const handleExportSummaryPdf = async () => {
    if (!summary) return
    const response = await summariesApi.exportPdf(summary.id)
    downloadBlob(new Blob([response.data]), `telescope-summary-${summary.id}.pdf`)
  }

  const chartPath = useMemo(() => {
    if (!messagesByDay || messagesByDay.length < 2) return ''
    const width = 320
    const height = 90
    const padding = 10
    const counts = messagesByDay.map((point) => point.count)
    const max = Math.max(...counts, 1)
    const step = (width - padding * 2) / (messagesByDay.length - 1)
    return messagesByDay
      .map((point, index) => {
        const x = padding + index * step
        const y = height - padding - (point.count / max) * (height - padding * 2)
        return `${index === 0 ? 'M' : 'L'}${x},${y}`
      })
      .join(' ')
  }, [messagesByDay])

  const maxChannelCount = Math.max(
    ...(messagesByChannel?.map((channel) => channel.count) || [1])
  )

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleExportMessages}
            className="px-3 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white hover:bg-gray-50"
          >
            Export Messages CSV
          </button>
          <button
            onClick={handleExportStats}
            className="px-3 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white hover:bg-gray-50"
          >
            Export Stats CSV
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-3xl font-bold text-blue-600">
                  {overview?.active_channels ?? channels?.length ?? 0}
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Active Channels
                  </dt>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-3xl font-bold text-green-600">
                  {overview?.total_messages ?? messagesData?.total ?? 0}
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Messages
                  </dt>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-3xl font-bold text-purple-600">
                  {overview?.messages_last_24h ?? summary?.message_count ?? 0}
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Messages (24h)
                  </dt>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900">Messages by Day</h3>
          {messagesByDay && messagesByDay.length > 1 ? (
            <svg width="100%" height="120" viewBox="0 0 340 110" className="mt-4">
              <path d={chartPath} fill="none" stroke="#2563eb" strokeWidth="3" />
            </svg>
          ) : (
            <p className="text-sm text-gray-500 mt-4">Not enough data yet.</p>
          )}
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900">Top Channels</h3>
          <div className="mt-4 space-y-3">
            {messagesByChannel && messagesByChannel.length > 0 ? (
              messagesByChannel.map((channel) => (
                <div key={channel.channel_id}>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>{channel.channel_title}</span>
                    <span>{channel.count}</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded">
                    <div
                      className="h-2 bg-blue-600 rounded"
                      style={{ width: `${(channel.count / maxChannelCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">No channel stats available yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Daily Summary */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Daily Summary</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleExportSummaryPdf}
                disabled={!summary}
                className="px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Export PDF
              </button>
              <button
                onClick={generateSummary}
                disabled={isGenerating}
                className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? 'Generating...' : 'Generate New'}
              </button>
            </div>
          </div>

          {summaryLoading ? (
            <div className="text-gray-500">Loading summary...</div>
          ) : summary ? (
            <div>
              <div className="text-sm text-gray-500 mb-2">
                Generated {new Date(summary.generated_at).toLocaleString()}
              </div>
              {summary.content_html ? (
                <div
                  className="prose max-w-none text-gray-700"
                  dangerouslySetInnerHTML={{ __html: summary.content_html }}
                />
              ) : (
                <div className="prose max-w-none">
                  <p className="text-gray-700 whitespace-pre-wrap">{summary.content}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-gray-500">
              No summary available yet. Add some channels and wait for messages to be collected,
              then generate your first summary.
            </div>
          )}
        </div>
      </div>

      {/* Recent Messages Preview */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Messages</h3>
          {messagesData?.messages && messagesData.messages.length > 0 ? (
            <div className="space-y-4">
              {messagesData.messages.map((message) => (
                <div key={message.id} className="border-l-4 border-blue-500 pl-4">
                  <div className="text-sm text-gray-900">
                    {message.translated_text || message.original_text}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(message.published_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500">No messages yet. Add channels to get started.</div>
          )}
        </div>
      </div>
    </div>
  )
}
