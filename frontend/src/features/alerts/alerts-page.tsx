import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Bell, Trash2, Pencil, Eye } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { alertsApi, collectionsApi } from '@/lib/api/client'
import type { Alert } from '@/lib/api/types'
import { Timestamp } from '@/components/common/timestamp'
import { CreateAlertDialog } from './create-alert-dialog'

export function AlertsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [editing, setEditing] = useState<Alert | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const alertsQuery = useQuery({
    queryKey: ['alerts'],
    queryFn: async () => (await alertsApi.list()).data,
  })

  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      alertsApi.update(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const deleteAlert = useMutation({
    mutationFn: (id: string) => alertsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      setDeleteId(null)
    },
  })

  const alerts = alertsQuery.data ?? []
  const collections = collectionsQuery.data ?? []

  const getCollectionName = (collectionId: string) =>
    collections.find((c) => c.id === collectionId)?.name ?? ''

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-foreground/60">{t('alerts.subtitle')}</p>
          <h2 className="text-2xl font-semibold">{t('alerts.title')}</h2>
        </div>
        <Button onClick={() => { setEditing(null); setCreateOpen(true) }}>
          <Bell className="mr-2 h-4 w-4" />
          {t('alerts.createAlert')}
        </Button>
      </div>

      {alertsQuery.isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}><CardContent className="h-24 animate-pulse py-6" /></Card>
          ))}
        </div>
      ) : alerts.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <Bell className="h-10 w-10 text-foreground/20" />
            <p className="text-sm text-foreground/60">{t('alerts.empty')}</p>
            <Button variant="outline" onClick={() => setCreateOpen(true)}>
              {t('alerts.createAlert')}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <Card key={alert.id}>
              <CardContent className="flex items-center gap-4 py-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-semibold truncate">{alert.name}</p>
                    <Badge variant={alert.is_active ? 'default' : 'muted'}>
                      {alert.is_active ? t('alerts.active') : t('alerts.paused')}
                    </Badge>
                    <Badge variant="outline">{alert.frequency}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-foreground/60">
                    {getCollectionName(alert.collection_id)}
                  </p>
                  {alert.keywords && alert.keywords.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {alert.keywords.map((kw) => (
                        <span key={kw} className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                          {kw}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="mt-1 text-xs text-foreground/40">
                    {t('alerts.lastTriggered')}: {alert.last_triggered_at ? <Timestamp value={alert.last_triggered_at} /> : t('alerts.never')}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="icon" onClick={() => navigate(`/alerts/${alert.id}`)} title={t('alerts.viewAlert')}>
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => { setEditing(alert); setCreateOpen(true) }} title={t('alerts.editAlert')}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost" size="icon"
                    onClick={() => toggleActive.mutate({ id: alert.id, is_active: !alert.is_active })}
                    title={alert.is_active ? t('alerts.paused') : t('alerts.active')}
                  >
                    <Bell className={`h-4 w-4 ${alert.is_active ? '' : 'text-foreground/30'}`} />
                  </Button>
                  {deleteId === alert.id ? (
                    <div className="flex items-center gap-1">
                      <Button variant="destructive" size="sm" onClick={() => deleteAlert.mutate(alert.id)} disabled={deleteAlert.isPending}>
                        {t('alerts.confirmDelete')}
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => setDeleteId(null)}>
                        {t('alerts.cancel')}
                      </Button>
                    </div>
                  ) : (
                    <Button variant="ghost" size="icon" onClick={() => setDeleteId(alert.id)} title={t('alerts.deleteAlert')}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <CreateAlertDialog
        open={createOpen}
        onOpenChange={(open) => { setCreateOpen(open); if (!open) setEditing(null) }}
        alert={editing}
        collections={collections}
      />
    </div>
  )
}
