import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { alertsApi, type Alert } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Timestamp } from '@/components/common/timestamp'
import { ConfirmDialog } from '@/components/common/confirm-dialog'

interface CollectionAlertsProps {
  collectionId: string
}

export function CollectionAlerts({ collectionId }: CollectionAlertsProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Alert | null>(null)
  const [name, setName] = useState('')
  const [keywords, setKeywords] = useState('')
  const [entities, setEntities] = useState('')
  const [minThreshold, setMinThreshold] = useState('1')
  const [frequency, setFrequency] = useState('daily')
  const [isActive, setIsActive] = useState(true)
  const [historyAlertId, setHistoryAlertId] = useState<string | null>(null)

  const alertsQuery = useQuery({
    queryKey: ['alerts', collectionId],
    queryFn: async () => (await alertsApi.list({ collection_id: collectionId })).data,
  })

  const createAlert = useMutation({
    mutationFn: () =>
      alertsApi.create({
        name,
        collection_id: collectionId,
        keywords: keywords
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
        entities: entities
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
        min_threshold: Number(minThreshold) || 1,
        frequency,
        is_active: isActive,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', collectionId] })
      setOpen(false)
    },
  })

  const updateAlert = useMutation({
    mutationFn: () =>
      alertsApi.update(editing?.id ?? '', {
        name,
        keywords: keywords
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
        entities: entities
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
        min_threshold: Number(minThreshold) || 1,
        frequency,
        is_active: isActive,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', collectionId] })
      setOpen(false)
      setEditing(null)
    },
  })

  const deleteAlert = useMutation({
    mutationFn: (id: string) => alertsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts', collectionId] }),
  })

  const triggersQuery = useQuery({
    queryKey: ['alert-triggers', historyAlertId],
    queryFn: async () => (await alertsApi.triggers(historyAlertId ?? '', { limit: 10 })).data,
    enabled: Boolean(historyAlertId),
  })

  useEffect(() => {
    if (!open) return
    if (!editing) {
      setName('')
      setKeywords('')
      setEntities('')
      setMinThreshold('1')
      setFrequency('daily')
      setIsActive(true)
      return
    }
    setName(editing.name)
    setKeywords((editing.keywords ?? []).join(', '))
    setEntities((editing.entities ?? []).join(', '))
    setMinThreshold(String(editing.min_threshold))
    setFrequency(editing.frequency)
    setIsActive(editing.is_active)
  }, [open, editing])

  const alerts = alertsQuery.data ?? []

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>{t('collections.alertsTitle')}</CardTitle>
          <p className="text-sm text-foreground/60">{t('collections.alertsSubtitle')}</p>
        </div>
        <Dialog
          open={open}
          onOpenChange={(nextOpen) => {
            setOpen(nextOpen)
            if (!nextOpen) {
              setEditing(null)
            }
          }}
        >
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              {t('collections.alertsCreate')}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editing ? t('collections.alertsEdit') : t('collections.alertsCreate')}
              </DialogTitle>
            </DialogHeader>
            <div className="mt-4 flex flex-col gap-3">
              <div className="flex flex-col gap-2">
                <Label htmlFor="alert-name">{t('collections.alertsName')}</Label>
                <Input id="alert-name" value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="alert-keywords">{t('collections.alertsKeywords')}</Label>
                <Input
                  id="alert-keywords"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="alert-entities">{t('collections.alertsEntities')}</Label>
                <Input
                  id="alert-entities"
                  value={entities}
                  onChange={(e) => setEntities(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="alert-threshold">{t('collections.alertsThreshold')}</Label>
                <Input
                  id="alert-threshold"
                  type="number"
                  min={1}
                  value={minThreshold}
                  onChange={(e) => setMinThreshold(e.target.value)}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {['realtime', 'hourly', 'daily'].map((value) => (
                  <Button
                    key={value}
                    variant={frequency === value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFrequency(value)}
                  >
                    {value}
                  </Button>
                ))}
              </div>
              <Button
                variant={isActive ? 'default' : 'outline'}
                size="sm"
                onClick={() => setIsActive((prev) => !prev)}
              >
                {isActive ? t('collections.alertsActive') : t('collections.alertsInactive')}
              </Button>
              <Button
                onClick={() => (editing ? updateAlert.mutate() : createAlert.mutate())}
                disabled={createAlert.isPending || updateAlert.isPending}
              >
                {t('collections.save')}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent className="space-y-3">
        {alerts.length ? (
          alerts.map((alert) => (
            <div key={alert.id} className="rounded-xl border border-border/60 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold">{alert.name}</p>
                  <p className="text-xs text-foreground/60">
                    {alert.frequency} ·{' '}
                    {t('collections.alertsThresholdLabel', { count: alert.min_threshold })}
                  </p>
                  {alert.last_triggered_at ? (
                    <p className="text-xs text-foreground/50">
                      {t('collections.alertsLastTriggered')}{' '}
                      <Timestamp value={alert.last_triggered_at} />
                    </p>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditing(alert)
                      setOpen(true)
                    }}
                  >
                    {t('collections.edit')}
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setHistoryAlertId(alert.id)}>
                    {t('collections.alertsHistory')}
                  </Button>
                  <ConfirmDialog
                    title={t('collections.alertsDeleteTitle')}
                    description={t('collections.alertsDeleteDescription')}
                    confirmText={t('collections.delete')}
                    cancelText={t('collections.cancel')}
                    variant="destructive"
                    onConfirm={() => deleteAlert.mutate(alert.id)}
                    triggerButton={
                      <Button variant="outline" size="sm">
                        {t('collections.delete')}
                      </Button>
                    }
                  />
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {(alert.keywords ?? []).map((keyword) => (
                  <Badge key={`${alert.id}-${keyword}`} variant="outline">
                    {keyword}
                  </Badge>
                ))}
                {(alert.entities ?? []).map((entity) => (
                  <Badge key={`${alert.id}-${entity}`} variant="outline">
                    {entity}
                  </Badge>
                ))}
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-foreground/60">{t('collections.alertsEmpty')}</p>
        )}
      </CardContent>
      <Dialog
        open={Boolean(historyAlertId)}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) setHistoryAlertId(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('collections.alertsHistory')}</DialogTitle>
          </DialogHeader>
          <div className="mt-4 space-y-3">
            {(triggersQuery.data ?? []).length ? (
              (triggersQuery.data ?? []).map((trigger) => (
                <div key={trigger.id} className="rounded-xl border border-border/60 p-3">
                  <p className="text-xs text-foreground/60">
                    <Timestamp value={trigger.triggered_at} />
                  </p>
                  <p className="text-sm">{trigger.summary ?? '-'}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-foreground/60">{t('collections.alertsHistoryEmpty')}</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
