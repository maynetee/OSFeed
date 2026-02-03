import { useEffect, useRef, useState, useCallback } from 'react'
import { api } from '@/lib/api/client'
import { Message, TranslationUpdate } from '@/lib/api/client'

interface UseMessageStreamOptions {
  enabled?: boolean
  channelId?: string
  channelIds?: string[]
  onMessages?: (messages: Message[], isRealtime: boolean) => void
  onTranslation?: (update: TranslationUpdate) => void
  onAlert?: (data: any) => void
}

export function useMessageStream(options: UseMessageStreamOptions = {}) {
  const { enabled = true, channelId, channelIds, onMessages, onTranslation, onAlert } = options
  const [isConnected, setIsConnected] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  const connect = useCallback(() => {
    if (!enabled) return

    // Cleanup previous connection
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    const controller = new AbortController()
    abortControllerRef.current = controller

    const params = new URLSearchParams({
      limit: '50',
      realtime: 'true',
    })

    if (channelId) params.append('channel_id', channelId)
    if (channelIds) channelIds.forEach(id => params.append('channel_ids', id))

    import('@/stores/user-store').then(({ useUserStore }) => {
      const token = useUserStore.getState().tokens?.accessToken
      
      fetch(`${api.defaults.baseURL}/api/messages/stream?${params}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Accept': 'text/event-stream',
        },
        signal: controller.signal,
      }).then(async (response) => {
        if (!response.ok) {
          setIsConnected(false)
          return
        }

        setIsConnected(true)
        const reader = response.body?.getReader()
        if (!reader) return

        const decoder = new TextDecoder()
        let buffer = ''
        const DATA_PREFIX_LEN = 6 // 'data: '.length

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Parse events inline using indexOf instead of split() to avoid
          // allocating an intermediate array on every chunk
          let delimIdx: number
          while ((delimIdx = buffer.indexOf('\n\n')) !== -1) {
            const event = buffer.substring(0, delimIdx)
            buffer = buffer.substring(delimIdx + 2)

            // Fast char-code check before startsWith to skip non-data lines cheaply
            if (event.length <= DATA_PREFIX_LEN || event.charCodeAt(0) !== 100 /* 'd' */) continue
            if (event.charCodeAt(5) !== 32 /* ' ' */) continue

            try {
              const payload = JSON.parse(event.substring(DATA_PREFIX_LEN))

              // Handle translation events
              if (payload.type === 'message:translated') {
                onTranslation?.(payload.data)
                continue
              }

              // Handle alert events
              if (payload.type === 'alert:triggered') {
                console.log('Alert received:', payload.data)
                onAlert?.(payload.data)
                continue
              }

              // Handle message events (existing behavior)
              if (payload.messages && payload.messages.length > 0) {
                onMessages?.(payload.messages, payload.type === 'realtime')
              }
            } catch (e) {
              console.error('Error parsing SSE data', e)
            }
          }
        }
      }).catch(err => {
        if (err.name !== 'AbortError') {
          console.error('SSE Error:', err)
          setIsConnected(false)
          setTimeout(connect, 5000)
        }
      })
    })

  }, [enabled, channelId, channelIds, onMessages, onTranslation, onAlert])

  useEffect(() => {
    connect()
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [connect])

  return { isConnected, reconnect: connect }
}
