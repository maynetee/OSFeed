import { useState, useCallback, useEffect, useRef } from 'react'
import { channelsApi } from '@/lib/api/client'

export interface RefreshState {
  lastRefresh: Date | null
  isRefreshing: boolean
  newCount: number
}

export interface UseMessagePollingOptions {
  interval?: number
  enabled?: boolean
  onNewMessages?: (count: number) => void
}

const DEFAULT_INTERVAL = 20_000 // 20 seconds
const MANUAL_REFRESH_POLL_INTERVAL = 1_000
const MANUAL_REFRESH_TIMEOUT = 30_000

export function useMessagePolling(
  refetchFn: () => Promise<unknown>,
  options: UseMessagePollingOptions = {},
) {
  const { interval = DEFAULT_INTERVAL, enabled = true } = options
  const [refreshState, setRefreshState] = useState<RefreshState>({
    lastRefresh: null,
    isRefreshing: false,
    newCount: 0,
  })

  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const isRefreshingRef = useRef(false)

  const doRefresh = useCallback(async () => {
    if (isRefreshingRef.current) return

    isRefreshingRef.current = true
    setRefreshState((prev) => ({ ...prev, isRefreshing: true }))

    try {
      await refetchFn()
      const now = new Date()
      setRefreshState({
        lastRefresh: now,
        isRefreshing: false,
        newCount: 0, // Reset count after successful refresh
      })
    } catch {
      setRefreshState((prev) => ({ ...prev, isRefreshing: false }))
    } finally {
      isRefreshingRef.current = false
    }
  }, [refetchFn])

  // Manual refresh
  const manualRefresh = useCallback(
    async (channelIds?: string[]) => {
      if (isRefreshingRef.current) return

      isRefreshingRef.current = true
      setRefreshState((prev) => ({ ...prev, isRefreshing: true }))

      try {
        const refreshResponse = await channelsApi.refresh(channelIds)
        const jobIds = refreshResponse.data.job_ids ?? []
        const startTime = Date.now()

        while (jobIds.length > 0) {
          const statusResponse = await channelsApi.getJobsStatus(jobIds)
          const jobs = statusResponse.data.jobs ?? []
          const completedJobs = new Set(
            jobs
              .filter((job) => job.status === 'completed' || job.status === 'failed')
              .map((job) => job.id),
          )
          const allDone = jobIds.every((id) => completedJobs.has(id))
          if (allDone) {
            break
          }
          if (Date.now() - startTime > MANUAL_REFRESH_TIMEOUT) {
            break
          }
          await new Promise((resolve) => setTimeout(resolve, MANUAL_REFRESH_POLL_INTERVAL))
        }

        await refetchFn()
        const now = new Date()
        setRefreshState({
          lastRefresh: now,
          isRefreshing: false,
          newCount: 0,
        })
      } catch {
        setRefreshState((prev) => ({ ...prev, isRefreshing: false }))
      } finally {
        isRefreshingRef.current = false
      }
    },
    [refetchFn],
  )

  // Set up polling interval
  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    // Initial refresh to set lastRefresh
    if (!refreshState.lastRefresh) {
      setRefreshState((prev) => ({
        ...prev,
        lastRefresh: new Date(),
      }))
    }

    intervalRef.current = setInterval(() => {
      // Only poll if tab is visible
      if (document.visibilityState === 'visible') {
        doRefresh()
      }
    }, interval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [enabled, interval, doRefresh, refreshState.lastRefresh])

  // Pause polling when tab is not visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && enabled) {
        // Refresh immediately when coming back to tab if stale
        const timeSinceRefresh = refreshState.lastRefresh
          ? Date.now() - refreshState.lastRefresh.getTime()
          : Infinity
        if (timeSinceRefresh > interval) {
          doRefresh()
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [enabled, interval, refreshState.lastRefresh, doRefresh])

  // Format last refresh timestamp with centiseconds
  const formatLastRefresh = useCallback((date: Date | null): string => {
    if (!date) return '--:--:--.--'

    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const seconds = date.getSeconds().toString().padStart(2, '0')
    const centiseconds = Math.floor(date.getMilliseconds() / 10)
      .toString()
      .padStart(2, '0')

    return `${hours}:${minutes}:${seconds}.${centiseconds}`
  }, [])

  // Format full timestamp with date
  const formatLastRefreshFull = useCallback(
    (date: Date | null): string | null => {
      if (!date) return null
      return `${date.toLocaleDateString()} ${formatLastRefresh(date)}`
    },
    [formatLastRefresh],
  )

  return {
    lastRefresh: refreshState.lastRefresh,
    lastRefreshFormatted: formatLastRefresh(refreshState.lastRefresh),
    lastRefreshFull: formatLastRefreshFull(refreshState.lastRefresh),
    isRefreshing: refreshState.isRefreshing,
    newMessageCount: refreshState.newCount,
    manualRefresh,
    pollingInterval: interval,
  }
}
