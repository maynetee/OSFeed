import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { analysisApi } from '@/lib/api/analysis'
import { collectionsApi } from '@/lib/api/collections'

interface TimelineGenerateModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TimelineGenerateModal({ open, onOpenChange }: TimelineGenerateModalProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [topic, setTopic] = useState('')
  const [collectionId, setCollectionId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const { data: collectionsData } = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
    enabled: open,
  })

  const generateMutation = useMutation({
    mutationFn: (params: { topic?: string; collection_id?: string; start_date?: string; end_date?: string }) =>
      analysisApi.generateTimeline(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timelines'] })
      onOpenChange(false)
      setTopic('')
      setCollectionId('')
      setStartDate('')
      setEndDate('')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const params: { topic?: string; collection_id?: string; start_date?: string; end_date?: string } = {}
    if (topic.trim()) params.topic = topic.trim()
    if (collectionId) params.collection_id = collectionId
    if (startDate) params.start_date = new Date(startDate).toISOString()
    if (endDate) params.end_date = new Date(endDate).toISOString()
    generateMutation.mutate(params)
  }

  const canSubmit = topic.trim() || collectionId

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('analysis.timeline.newTimeline')}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topic">{t('analysis.timeline.topic')}</Label>
            <Input
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder={t('analysis.timeline.topic')}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="collection">{t('analysis.timeline.collection')}</Label>
            <select
              id="collection"
              value={collectionId}
              onChange={(e) => setCollectionId(e.target.value)}
              className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
            >
              <option value="">—</option>
              {collectionsData?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="start-date">{t('analysis.timeline.dateRange')}</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end-date">&nbsp;</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="submit"
              disabled={!canSubmit || generateMutation.isPending}
            >
              {generateMutation.isPending
                ? t('analysis.timeline.generating')
                : t('analysis.timeline.generate')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
