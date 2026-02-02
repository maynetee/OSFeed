import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { exportsApi, messagesApi, statsApi } from '@/lib/api/client'
import { useTranslation } from 'react-i18next'

const downloadBlob = (data: Blob, filename: string) => {
  const url = window.URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

interface ExportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  filters?: {
    channel_ids?: string[]
    start_date?: string
    end_date?: string
    media_types?: string[]
  }
}

export function ExportDialog({ open, onOpenChange, filters }: ExportDialogProps) {
  const { t } = useTranslation()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{t('exports.dialogTitle')}</DialogTitle>
        </DialogHeader>
        <Card>
          <CardContent className="flex flex-col gap-4 py-6">
            <p className="text-sm text-foreground/70">{t('exports.dialogDescription')}</p>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                onClick={async () => {
                  const response = await exportsApi.messagesCsv(filters)
                  downloadBlob(response.data, 'messages.csv')
                }}
              >
                {t('exports.exportCsv')}
              </Button>
              <Button
                variant="outline"
                onClick={async () => {
                  const response = await messagesApi.exportPdf({
                    ...filters,
                    limit: 200,
                  })
                  downloadBlob(response.data, 'messages.pdf')
                }}
              >
                {t('exports.exportPdf')}
              </Button>
              <Button
                variant="outline"
                onClick={async () => {
                  const response = await messagesApi.exportHtml({
                    ...filters,
                    limit: 200,
                  })
                  downloadBlob(new Blob([response.data], { type: 'text/html' }), 'messages.html')
                }}
              >
                {t('exports.exportHtml')}
              </Button>
              <Button
                variant="outline"
                onClick={async () => {
                  const response = await statsApi.exportCsv(7)
                  downloadBlob(response.data, 'stats.csv')
                }}
              >
                {t('exports.exportStatsCsv')}
              </Button>
              <Button
                variant="outline"
                onClick={async () => {
                  const response = await statsApi.exportJson(7)
                  downloadBlob(response.data, 'stats.json')
                }}
              >
                {t('exports.exportStatsJson')}
              </Button>
            </div>
          </CardContent>
        </Card>
      </DialogContent>
    </Dialog>
  )
}
