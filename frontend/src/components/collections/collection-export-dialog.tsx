import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface CollectionExportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onExport: (params: {
    format: string
    start_date?: string
    end_date?: string
    limit?: number
  }) => void
}

export function CollectionExportDialog({
  open,
  onOpenChange,
  onExport,
}: CollectionExportDialogProps) {
  const { t } = useTranslation()
  const [format, setFormat] = useState('csv')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [limit, setLimit] = useState('200')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('collections.exportTitle')}</DialogTitle>
        </DialogHeader>
        <div className="mt-4 flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            {['csv', 'html', 'pdf'].map((value) => (
              <Button
                key={value}
                variant={format === value ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFormat(value)}
              >
                {value.toUpperCase()}
              </Button>
            ))}
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="startDate">{t('collections.exportStart')}</Label>
              <Input
                id="startDate"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="endDate">{t('collections.exportEnd')}</Label>
              <Input
                id="endDate"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="limit">{t('collections.exportLimit')}</Label>
            <Input
              id="limit"
              type="number"
              min={1}
              max={1000}
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
            />
          </div>
          <Button
            onClick={() =>
              onExport({
                format,
                start_date: startDate ? new Date(startDate).toISOString() : undefined,
                end_date: endDate ? new Date(endDate).toISOString() : undefined,
                limit: Number(limit) || 200,
              })
            }
          >
            {t('collections.exportAction')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
