import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import type { Summary } from '@/lib/api/client'

interface DigestCardProps {
  digest: Summary
  onOpen?: (id: string) => void
  onExportPdf?: (id: string) => void
  onExportHtml?: (id: string) => void
}

export function DigestCard({ digest, onOpen, onExportPdf, onExportHtml }: DigestCardProps) {
  return (
    <Card>
      <CardContent className="flex flex-wrap items-center justify-between gap-4 py-6">
        <div>
          <p className="text-sm font-semibold">{digest.title ?? 'Daily Digest'}</p>
          <p className="text-xs text-foreground/60">
            {digest.message_count} messages · {digest.duplicates_filtered ?? 0}% duplicatas filtres
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => onOpen?.(digest.id)}>
            Ouvrir
          </Button>
          <Button variant="outline" onClick={() => onExportPdf?.(digest.id)}>
            PDF
          </Button>
          <Button variant="outline" onClick={() => onExportHtml?.(digest.id)}>
            HTML
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
