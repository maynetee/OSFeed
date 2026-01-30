import { memo, useCallback, useState } from 'react'
import { ExternalLink } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { useUserStore } from '@/stores/user-store'

interface MediaPreviewProps {
  messageId: string
  mediaType: 'photo' | 'video'
  channelUsername: string
  telegramMessageId: number
}

const API_URL = import.meta.env.VITE_API_URL || ''

export const MediaPreview = memo(function MediaPreview({
  messageId,
  mediaType,
  channelUsername,
  telegramMessageId,
}: MediaPreviewProps) {
  const { t } = useTranslation()
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  const tokens = useUserStore((s) => s.tokens)
  const telegramLink = `https://t.me/${channelUsername}/${telegramMessageId}`

  const mediaUrl = `${API_URL}/api/messages/${messageId}/media`

  const handleLoad = useCallback(() => setIsLoading(false), [])
  const handleError = useCallback(() => {
    setIsLoading(false)
    setHasError(true)
  }, [])
  const handleRetry = useCallback(() => {
    setHasError(false)
    setIsLoading(true)
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

  const authHeaders: Record<string, string> = {}
  if (tokens?.accessToken) {
    authHeaders['Authorization'] = `Bearer ${tokens.accessToken}`
  }

  return (
    <div className="relative overflow-hidden rounded-lg border border-border/60">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="h-48 w-full animate-pulse rounded-lg bg-muted" />
        </div>
      )}
      {mediaType === 'photo' ? (
        <AuthImage
          src={mediaUrl}
          token={tokens?.accessToken}
          onLoad={handleLoad}
          onError={handleError}
          className={`max-h-[500px] w-auto object-contain ${isLoading ? 'invisible' : ''}`}
          alt=""
        />
      ) : (
        <AuthVideo
          src={mediaUrl}
          token={tokens?.accessToken}
          onLoadedData={handleLoad}
          onError={handleError}
          className={`max-h-[500px] w-full ${isLoading ? 'invisible' : ''}`}
          controls
        />
      )}
    </div>
  )
})

/**
 * Image component that fetches via an authenticated request and displays
 * using an object URL. This avoids the need for cookie-based auth on the
 * media proxy endpoint.
 */
function AuthImage({
  src,
  token,
  onLoad,
  onError,
  className,
  alt,
}: {
  src: string
  token?: string
  onLoad: () => void
  onError: () => void
  className?: string
  alt?: string
}) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null)

  // Fetch image with auth header and create object URL
  const imgRef = useCallback(
    (node: HTMLImageElement | null) => {
      if (!node || objectUrl) return

      const controller = new AbortController()
      fetch(src, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: controller.signal,
      })
        .then((res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`)
          return res.blob()
        })
        .then((blob) => {
          const url = URL.createObjectURL(blob)
          setObjectUrl(url)
          onLoad()
        })
        .catch((err) => {
          if (err.name !== 'AbortError') onError()
        })

      return () => controller.abort()
    },
    [src, token, objectUrl, onLoad, onError],
  )

  if (objectUrl) {
    return <img src={objectUrl} className={className} alt={alt ?? ''} />
  }

  return <img ref={imgRef} className={className} alt={alt ?? ''} />
}

/**
 * Video component that fetches via an authenticated request and displays
 * using an object URL.
 */
function AuthVideo({
  src,
  token,
  onLoadedData,
  onError,
  className,
  controls,
}: {
  src: string
  token?: string
  onLoadedData: () => void
  onError: () => void
  className?: string
  controls?: boolean
}) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null)

  const videoRef = useCallback(
    (node: HTMLVideoElement | null) => {
      if (!node || objectUrl) return

      const controller = new AbortController()
      fetch(src, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: controller.signal,
      })
        .then((res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`)
          return res.blob()
        })
        .then((blob) => {
          const url = URL.createObjectURL(blob)
          setObjectUrl(url)
        })
        .catch((err) => {
          if (err.name !== 'AbortError') onError()
        })

      return () => controller.abort()
    },
    [src, token, objectUrl, onError],
  )

  if (objectUrl) {
    return (
      <video
        src={objectUrl}
        className={className}
        controls={controls}
        onLoadedData={onLoadedData}
        onError={onError}
      />
    )
  }

  return <video ref={videoRef} className={className} controls={controls} />
}

// Keep the old name as re-export for backwards compat during transition
export const TelegramEmbed = MediaPreview
