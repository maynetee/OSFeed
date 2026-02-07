import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, Bell } from 'lucide-react'

import { PageTransition } from '@/components/layout/page-transition'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { alertsApi } from '@/lib/api/client'
import { Timestamp } from '@/components/common/timestamp'

export function AlertDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const alertQuery = useQuery({
    queryKey: ['alerts', id],
    queryFn: async () => {
      const list = (await alertsApi.list()).data
      return list.find((a) => a.id === id) ?? null
    },
    enabled: !!id,
  })

  const triggersQuery = useQuery({
    queryKey: ['alerts', id, 'triggers'],
    queryFn: async () => (await alertsApi.triggers(id!, { limit: 50 })).data,
    enabled: !!id,
  })

  const alert = alertQuery.data
  const triggers = triggersQuery.data ?? []

  if (alertQuery.isLoading) {
    return <div className="p-8 text-sm text-foreground/60">{t('common.loading')}</div>
  }

  if (!alert) {
    return (
      <div className="flex flex-col items-center gap-4 py-12">
        <p className="text-sm text-foreground/60">{t('alerts.error')}</p>
        <Button variant="outline" onClick={() => navigate('/alerts')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          {t('alerts.backToAlerts')}
        </Button>
      </div>
    )
  }

  return (
    <PageTransition>
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate('/alerts')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-2xl font-semibold">{alert.name}</h2>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={alert.is_active ? 'default' : 'muted'}>
                {alert.is_active ? t('alerts.active') : t('alerts.paused')}
              </Badge>
              <Badge variant="outline">{alert.frequency}</Badge>
              {alert.match_mode && (
                <Badge variant="outline">
                  {alert.match_mode === 'all' ? t('alerts.matchAll') : t('alerts.matchAny')}
                </Badge>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="py-4">
              <p className="text-xs text-foreground/60">{t('alerts.totalTriggers')}</p>
              <p className="text-2xl font-semibold">{triggers.length}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <p className="text-xs text-foreground/60">{t('alerts.lastTriggered')}</p>
              <p className="text-sm font-medium">
                {alert.last_triggered_at ? (
                  <Timestamp value={alert.last_triggered_at} />
                ) : (
                  t('alerts.never')
                )}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <p className="text-xs text-foreground/60">{t('alerts.keywords')}</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {(alert.keywords ?? []).map((kw) => (
                  <span
                    key={kw}
                    className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                  >
                    {kw}
                  </span>
                ))}
                {(!alert.keywords || alert.keywords.length === 0) && (
                  <span className="text-xs text-foreground/40">&mdash;</span>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-3">{t('alerts.recentTriggers')}</h3>
          {triggersQuery.isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <Card key={i}>
                  <CardContent className="h-16 animate-pulse py-4" />
                </Card>
              ))}
            </div>
          ) : triggers.length === 0 ? (
            <Card>
              <CardContent className="flex items-center gap-3 py-8 text-center justify-center">
                <Bell className="h-5 w-5 text-foreground/20" />
                <p className="text-sm text-foreground/60">{t('alerts.noTriggers')}</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {triggers.map((trigger) => (
                <Card key={trigger.id}>
                  <CardContent className="flex items-center justify-between py-3">
                    <div>
                      <p className="text-sm font-medium">
                        {trigger.summary ?? t('alerts.triggered')}
                      </p>
                      <p className="text-xs text-foreground/50">
                        {trigger.message_ids.length} {t('alerts.matchedMessages')}
                      </p>
                    </div>
                    <p className="text-xs text-foreground/40">
                      <Timestamp value={trigger.triggered_at} />
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  )
}
