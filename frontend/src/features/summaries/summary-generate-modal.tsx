import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Loader2, Sparkles } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { summariesApi } from '@/lib/api/summaries'
import type { SummaryResponse } from '@/lib/api/summaries'
import { SummaryDisplay } from './summary-display'

interface SummaryGenerateModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  collectionId?: string
  channelIds?: string[]
}

export function SummaryGenerateModal({
  open,
  onOpenChange,
  collectionId,
  channelIds,
}: SummaryGenerateModalProps) {
  const { t } = useTranslation()
  const [dateRange, setDateRange] = useState<string>('7d')
  const [maxMessages, setMaxMessages] = useState<number>(100)
  const [result, setResult] = useState<SummaryResponse | null>(null)

  const generateMutation = useMutation({
    mutationFn: () =>
      summariesApi.generate({
        collection_id: collectionId,
        channel_ids: !collectionId ? channelIds : undefined,
        date_range: dateRange,
        max_messages: maxMessages,
      }),
    onSuccess: (response) => {
      setResult(response.data)
    },
  })

  const handleClose = (nextOpen: boolean) => {
    if (!nextOpen) {
      setResult(null)
      generateMutation.reset()
    }
    onOpenChange(nextOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            {t('summaries.generate')}
          </DialogTitle>
          <DialogDescription>
            {result ? t('summaries.executiveSummary') : t('summaries.generatingDescription')}
          </DialogDescription>
        </DialogHeader>

        {!result && !generateMutation.isPending && (
          <div className="flex flex-col gap-4 py-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium">{t('summaries.dateRange')}</label>
              <div className="flex gap-2">
                {(['24h', '7d', '30d'] as const).map((range) => (
                  <Button
                    key={range}
                    variant={dateRange === range ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setDateRange(range)}
                  >
                    {t(`summaries.dateRange${range.charAt(0).toUpperCase() + range.slice(1)}`)}
                  </Button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium">
                {t('summaries.maxMessages')}
              </label>
              <div className="flex gap-2">
                {[50, 100, 200].map((count) => (
                  <Button
                    key={count}
                    variant={maxMessages === count ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setMaxMessages(count)}
                  >
                    {count}
                  </Button>
                ))}
              </div>
            </div>

            <Button className="mt-2 gap-2" onClick={() => generateMutation.mutate()}>
              <Sparkles className="h-4 w-4" />
              {t('summaries.generate')}
            </Button>

            {generateMutation.isError && (
              <p className="text-sm text-danger">{t('summaries.error')}</p>
            )}
          </div>
        )}

        {generateMutation.isPending && (
          <div className="flex flex-col items-center gap-3 py-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-foreground/60">{t('summaries.generating')}</p>
          </div>
        )}

        {result && <SummaryDisplay summary={result} />}
      </DialogContent>
    </Dialog>
  )
}
