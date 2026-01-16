import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { exportsApi, statsApi } from '@/lib/api/client'

const downloadBlob = (data: Blob, filename: string) => {
  const url = window.URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

export function ExportsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-sm text-foreground/60">Exporter vos analyses</p>
        <h2 className="text-2xl font-semibold">Exports</h2>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-4 py-6">
          <p className="text-sm">Choisissez un format pour partager vos signaux.</p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={async () => {
                const response = await exportsApi.messagesCsv()
                downloadBlob(response.data, 'messages.csv')
              }}
            >
              Exporter CSV
            </Button>
            <Button
              variant="outline"
              onClick={async () => {
                const response = await statsApi.exportCsv(7)
                downloadBlob(response.data, 'stats.csv')
              }}
            >
              Exporter Stats CSV
            </Button>
            <Button variant="outline">Exporter PDF</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
