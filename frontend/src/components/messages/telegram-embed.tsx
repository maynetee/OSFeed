import { memo, useCallback, useEffect, useRef, useState } from 'react'
import { ExternalLink } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { useUiStore } from '@/stores/ui-store'

interface TelegramEmbedProps {
  channelUsername: string
  messageId: number
}

const prefersDark = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches

export const TelegramEmbed = memo(function TelegramEmbed({
  channelUsername,
  messageId,
}: TelegramEmbedProps) {
  const { t } = useTranslation()
  const containerRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const theme = useUiStore((state) => state.theme)

  const isDarkMode = theme === 'system' ? prefersDark() : theme === 'dark'
  const telegramLink = `https://t.me/${channelUsername}/${messageId}`

  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    // Clear previous content
    container.innerHTML = ''
    setIsLoading(true)
    setHasError(false)

    // Create script element
    const script = document.createElement('script')
    script.src = 'https://telegram.org/js/telegram-widget.js?22'
    script.async = true
    script.setAttribute('data-telegram-post', `${channelUsername}/${messageId}`)
    script.setAttribute('data-width', '100%')
    script.setAttribute('data-userpic', 'false')
    if (isDarkMode) {
      script.setAttribute('data-dark', '1')
    }

    // Set up load timeout to detect failures
    const timeoutId = setTimeout(() => {
      // Check if iframe was created (widget loaded successfully)
      const iframe = container.querySelector('iframe')
      if (!iframe) {
        setHasError(true)
      }
      setIsLoading(false)
    }, 5000)

    // Listen for iframe load event
    const handleLoad = () => {
      clearTimeout(timeoutId)
      setIsLoading(false)
    }

    // Use MutationObserver to detect when iframe is added
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        for (const node of mutation.addedNodes) {
          if (node instanceof HTMLIFrameElement) {
            node.addEventListener('load', handleLoad)
            // Iframe was added, widget is loading
            setIsLoading(false)
            observer.disconnect()
            return
          }
        }
      }
    })

    observer.observe(container, { childList: true, subtree: true })

    script.onerror = () => {
      clearTimeout(timeoutId)
      setHasError(true)
      setIsLoading(false)
    }

    container.appendChild(script)

    return () => {
      clearTimeout(timeoutId)
      observer.disconnect()
      container.innerHTML = ''
    }
  }, [channelUsername, messageId, isDarkMode, retryCount])

  const handleRetry = useCallback(() => {
    setHasError(false)
    setIsLoading(true)
    setRetryCount((c) => c + 1)
  }, [])

  if (hasError) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-lg border border-border/60 bg-muted/40 p-4">
        <p className="text-sm text-foreground/60">{t('messages.mediaAvailableOnTelegram')}</p>
        <div className="flex gap-2">
          <Button asChild variant="outline" size="sm">
            <a href={telegramLink} target="_blank" rel="noreferrer">
              <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
              {t('messages.openTelegram')}
            </a>
          </Button>
          <Button variant="ghost" size="sm" onClick={handleRetry}>
            {t('messages.retry')}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="relative min-h-[100px]">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="h-48 w-full animate-pulse rounded-lg bg-muted" />
        </div>
      )}
      <div ref={containerRef} className={isLoading ? 'opacity-0' : 'opacity-100'} />
    </div>
  )
})
