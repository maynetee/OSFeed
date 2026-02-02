import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bell } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { alertsApi } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Timestamp } from '@/components/common/timestamp'

export function NotificationCenter() {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)

  const triggersQuery = useQuery({
    queryKey: ['alerts', 'recent'],
    queryFn: async () => (await alertsApi.recentTriggers({ limit: 10 })).data,
  })

  const triggers = triggersQuery.data ?? []

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon" aria-label={t('alerts.notifications')}>
          <Bell className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('alerts.notifications')}</DialogTitle>
        </DialogHeader>
        <div className="mt-4 space-y-3">
          {triggersQuery.isLoading && !triggers.length ? (
            <p className="text-sm text-foreground/60">{t('common.loading')}</p>
          ) : triggers.length ? (
            triggers.map((trigger) => (
              <div key={trigger.id} className="rounded-xl border border-border/60 p-3">
                <p className="text-sm font-semibold">{t('alerts.triggered')}</p>
                <p className="text-xs text-foreground/60">{trigger.summary ?? '-'}</p>
                <p className="text-xs text-foreground/60">
                  <Timestamp value={trigger.triggered_at} />
                </p>
              </div>
            ))
          ) : (
            <p className="text-sm text-foreground/60">{t('alerts.empty')}</p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
