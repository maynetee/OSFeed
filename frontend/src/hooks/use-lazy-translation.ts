import { useCallback, useEffect, useRef } from 'react'
import { messagesApi, Message } from '@/lib/api/client'

interface UseLazyTranslationOptions {
  messages: Message[]
  enabled?: boolean
}

export function useLazyTranslation({ messages, enabled = true }: UseLazyTranslationOptions) {
  // Track messages currently being translated
  const translatingRef = useRef<Set<string>>(new Set())
  // Track messages that failed translation (don't retry forever)
  const failedRef = useRef<Set<string>>(new Set())
  // Debounce timer
  const debounceRef = useRef<NodeJS.Timeout | null>(null)

  const MAX_CONCURRENT = 5

  const translateMessage = useCallback(async (messageId: string) => {
    if (translatingRef.current.size >= MAX_CONCURRENT) return false
    if (translatingRef.current.has(messageId)) return false
    if (failedRef.current.has(messageId)) return false

    translatingRef.current.add(messageId)

    try {
      await messagesApi.translateById(messageId)
      return true
    } catch (error) {
      console.error(`Failed to translate message ${messageId}:`, error)
      failedRef.current.add(messageId)
      return false
    } finally {
      translatingRef.current.delete(messageId)
    }
  }, [])

  const checkAndTranslate = useCallback(() => {
    if (!enabled) return

    // Find messages that need translation
    const needsTranslation = messages.filter(
      (msg) =>
        msg.needs_translation &&
        !msg.translated_text &&
        !translatingRef.current.has(msg.id) &&
        !failedRef.current.has(msg.id)
    )

    // Translate up to MAX_CONCURRENT messages
    const toTranslate = needsTranslation.slice(0, MAX_CONCURRENT - translatingRef.current.size)

    for (const msg of toTranslate) {
      translateMessage(msg.id)
    }
  }, [enabled, messages, translateMessage])

  // Debounced trigger for translation
  const triggerTranslation = useCallback(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    debounceRef.current = setTimeout(() => {
      checkAndTranslate()
    }, 200) // 200ms debounce
  }, [checkAndTranslate])

  // Trigger translation check when messages change
  useEffect(() => {
    triggerTranslation()
  }, [triggerTranslation])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [])

  return {
    translatingCount: translatingRef.current.size,
    triggerTranslation,
  }
}
