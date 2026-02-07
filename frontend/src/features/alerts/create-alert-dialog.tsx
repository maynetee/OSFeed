import { useState, useEffect, KeyboardEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { alertsApi } from '@/lib/api/client'
import type { Alert, Collection } from '@/lib/api/types'

interface CreateAlertDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  alert: Alert | null
  collections: Collection[]
}

export function CreateAlertDialog({ open, onOpenChange, alert, collections }: CreateAlertDialogProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const isEdit = !!alert

  const [name, setName] = useState('')
  const [keywords, setKeywords] = useState<string[]>([])
  const [keywordInput, setKeywordInput] = useState('')
  const [matchMode, setMatchMode] = useState('any')
  const [collectionId, setCollectionId] = useState('')
  const [entities, setEntities] = useState<string[]>([])
  const [entityInput, setEntityInput] = useState('')
  const [channels, setChannels] = useState<string[]>(['in_app'])
  const [frequency, setFrequency] = useState('daily')
  const [minThreshold, setMinThreshold] = useState(1)
  const [isActive, setIsActive] = useState(true)

  useEffect(() => {
    if (alert) {
      setName(alert.name)
      setKeywords(alert.keywords ?? [])
      setMatchMode(alert.match_mode ?? 'any')
      setCollectionId(alert.collection_id)
      setEntities(alert.entities ?? [])
      setChannels(alert.notification_channels ?? ['in_app'])
      setFrequency(alert.frequency)
      setMinThreshold(alert.min_threshold)
      setIsActive(alert.is_active)
    } else {
      setName('')
      setKeywords([])
      setMatchMode('any')
      setCollectionId(collections[0]?.id ?? '')
      setEntities([])
      setChannels(['in_app'])
      setFrequency('daily')
      setMinThreshold(1)
      setIsActive(true)
    }
  }, [alert, open, collections])

  const createMutation = useMutation({
    mutationFn: (payload: Parameters<typeof alertsApi.create>[0]) => alertsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      onOpenChange(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof alertsApi.update>[1] }) =>
      alertsApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      onOpenChange(false)
    },
  })

  const handleKeywordKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if ((e.key === 'Enter' || e.key === ',') && keywordInput.trim()) {
      e.preventDefault()
      const kw = keywordInput.trim().replace(/,$/, '')
      if (kw && !keywords.includes(kw)) {
        setKeywords([...keywords, kw])
      }
      setKeywordInput('')
    }
  }

  const handleEntityKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if ((e.key === 'Enter' || e.key === ',') && entityInput.trim()) {
      e.preventDefault()
      const ent = entityInput.trim().replace(/,$/, '')
      if (ent && !entities.includes(ent)) {
        setEntities([...entities, ent])
      }
      setEntityInput('')
    }
  }

  const toggleChannel = (ch: string) => {
    setChannels((prev) =>
      prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch]
    )
  }

  const handleSubmit = () => {
    const payload = {
      name,
      collection_id: collectionId,
      keywords,
      entities: entities.length ? entities : undefined,
      match_mode: matchMode,
      min_threshold: minThreshold,
      frequency,
      notification_channels: channels,
      is_active: isActive,
    }

    if (isEdit && alert) {
      updateMutation.mutate({ id: alert.id, payload })
    } else {
      createMutation.mutate(payload)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? t('alerts.editAlert') : t('alerts.createAlert')}</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4 mt-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="alert-name">{t('alerts.name')}</Label>
            <Input id="alert-name" value={name} onChange={(e) => setName(e.target.value)} placeholder={t('alerts.namePlaceholder')} />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="alert-collection">{t('alerts.collection')}</Label>
            <select
              id="alert-collection"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
              value={collectionId}
              onChange={(e) => setCollectionId(e.target.value)}
            >
              <option value="">{t('alerts.selectCollection')}</option>
              {collections.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>{t('alerts.keywords')}</Label>
            <div className="flex flex-wrap gap-1 mb-1">
              {keywords.map((kw) => (
                <span key={kw} className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                  {kw}
                  <button type="button" onClick={() => setKeywords(keywords.filter((k) => k !== kw))}><X className="h-3 w-3" /></button>
                </span>
              ))}
            </div>
            <Input value={keywordInput} onChange={(e) => setKeywordInput(e.target.value)} onKeyDown={handleKeywordKeyDown} placeholder={t('alerts.keywordsPlaceholder')} />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>{t('alerts.matchMode')}</Label>
            <div className="flex gap-3">
              <label className="flex items-center gap-1.5 text-sm">
                <input type="radio" name="match_mode" value="any" checked={matchMode === 'any'} onChange={() => setMatchMode('any')} className="accent-primary" />
                {t('alerts.matchAny')}
              </label>
              <label className="flex items-center gap-1.5 text-sm">
                <input type="radio" name="match_mode" value="all" checked={matchMode === 'all'} onChange={() => setMatchMode('all')} className="accent-primary" />
                {t('alerts.matchAll')}
              </label>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>{t('alerts.entities')}</Label>
            <div className="flex flex-wrap gap-1 mb-1">
              {entities.map((ent) => (
                <span key={ent} className="inline-flex items-center gap-1 rounded-full bg-secondary px-2 py-0.5 text-xs">
                  {ent}
                  <button type="button" onClick={() => setEntities(entities.filter((e) => e !== ent))}><X className="h-3 w-3" /></button>
                </span>
              ))}
            </div>
            <Input value={entityInput} onChange={(e) => setEntityInput(e.target.value)} onKeyDown={handleEntityKeyDown} placeholder={t('alerts.entitiesPlaceholder')} />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>{t('alerts.notificationChannels')}</Label>
            <div className="flex gap-3">
              <label className="flex items-center gap-1.5 text-sm">
                <input type="checkbox" checked={channels.includes('in_app')} onChange={() => toggleChannel('in_app')} className="accent-primary" />
                {t('alerts.inApp')}
              </label>
              <label className="flex items-center gap-1.5 text-sm">
                <input type="checkbox" checked={channels.includes('email')} onChange={() => toggleChannel('email')} className="accent-primary" />
                {t('alerts.email')}
              </label>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="alert-frequency">{t('alerts.frequency')}</Label>
            <select id="alert-frequency" className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={frequency} onChange={(e) => setFrequency(e.target.value)}>
              <option value="realtime">{t('alerts.frequencyRealtime')}</option>
              <option value="hourly">{t('alerts.frequencyHourly')}</option>
              <option value="daily">{t('alerts.frequencyDaily')}</option>
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="alert-threshold">{t('alerts.threshold')}</Label>
            <Input id="alert-threshold" type="number" min={1} value={minThreshold} onChange={(e) => setMinThreshold(Number(e.target.value))} />
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} className="accent-primary" />
            {t('alerts.active')}
          </label>

          <Button onClick={handleSubmit} disabled={isPending || !name || !collectionId}>
            {isEdit ? t('alerts.editAlert') : t('alerts.createAlert')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
