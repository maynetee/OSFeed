import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, Check, CheckCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import { notificationsApi } from '@/lib/api/notifications'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Timestamp } from '@/components/common/timestamp'
import { useMessageStream } from '@/hooks/use-message-stream'

export function NotificationCenter() {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const notificationsQuery = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => (await notificationsApi.list({ limit: 20 })).data,
  })

  const unreadQuery = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: async () => (await notificationsApi.unreadCount()).data,
    refetchInterval: 30_000,
  })

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const markAllRead = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  useMessageStream({
    enabled: true,
    onAlert: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const notifications = notificationsQuery.data?.notifications ?? []
  const unreadCount = unreadQuery.data?.count ?? 0

  const handleClick = (notification: (typeof notifications)[0]) => {
    if (!notification.is_read) {
      markRead.mutate(notification.id)
    }
    if (notification.link) {
      setOpen(false)
      navigate(notification.link)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon" aria-label={t('alerts.notifications')} className="relative">
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-semibold text-primary-foreground">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>{t('alerts.notifications')}</DialogTitle>
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs"
                onClick={() => markAllRead.mutate()}
                disabled={markAllRead.isPending}
              >
                <CheckCheck className="mr-1 h-3 w-3" />
                {t('alerts.markAllRead')}
              </Button>
            )}
          </div>
        </DialogHeader>
        <div className="mt-4 max-h-[60vh] space-y-2 overflow-y-auto">
          {notificationsQuery.isError ? (
            <p className="text-sm text-destructive">{t('alerts.error')}</p>
          ) : notificationsQuery.isLoading && !notifications.length ? (
            <p className="text-sm text-foreground/60">{t('common.loading')}</p>
          ) : notifications.length ? (
            notifications.map((n) => (
              <button
                key={n.id}
                type="button"
                onClick={() => handleClick(n)}
                className={`w-full rounded-xl border p-3 text-left transition hover:bg-accent/50 ${
                  n.is_read ? 'border-border/40 opacity-60' : 'border-primary/20 bg-primary/5'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold">{n.title}</p>
                  {!n.is_read && (
                    <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
                  )}
                </div>
                {n.body && <p className="mt-0.5 text-xs text-foreground/60">{n.body}</p>}
                <p className="mt-1 text-xs text-foreground/40">
                  <Timestamp value={n.created_at} />
                </p>
              </button>
            ))
          ) : (
            <div className="flex flex-col items-center gap-2 py-8">
              <Check className="h-6 w-6 text-foreground/20" />
              <p className="text-sm text-foreground/60">{t('alerts.noNotifications')}</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
