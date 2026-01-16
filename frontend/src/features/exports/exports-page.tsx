import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
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

export function ExportsPage() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-sm text-foreground/60">{t('exports.subtitle')}</p>
        <h2 className="text-2xl font-semibold">{t('exports.title')}</h2>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-4 py-6">
          <p className="text-sm">{t('exports.description')}</p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={async () => {
                const response = await exportsApi.messagesCsv()
                downloadBlob(response.data, 'messages.csv')
              }}
            >
              {t('exports.exportCsv')}
            </Button>
            <Button
              variant="outline"
              onClick={async () => {
                const response = await messagesApi.exportPdf({ limit: 200 })
                downloadBlob(response.data, 'messages.pdf')
              }}
            >
              {t('exports.exportPdf')}
            </Button>
            <Button
              variant="outline"
              onClick={async () => {
                const response = await messagesApi.exportHtml({ limit: 200 })
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
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
