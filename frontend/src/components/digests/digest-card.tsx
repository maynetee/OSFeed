import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import type { Summary } from '@/lib/api/client'
import { useTranslation } from 'react-i18next'

interface DigestCardProps {
  digest: Summary
  onOpen?: (id: string) => void
  onExportPdf?: (id: string) => void
  onExportHtml?: (id: string) => void
}

export function DigestCard({ digest, onOpen, onExportPdf, onExportHtml }: DigestCardProps) {
  const { t } = useTranslation()

  return (
    <Card className="animate-rise-in">
      <CardContent className="flex flex-wrap items-center justify-between gap-4 py-6">
        <div>
          <p className="text-sm font-semibold">{digest.title ?? t('digests.title')}</p>
          <p className="text-xs text-foreground/60">
            {t('digests.cardMeta', {
              messages: digest.message_count,
              duplicates: digest.duplicates_filtered ?? 0,
            })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => onOpen?.(digest.id)}>
            {t('common.open')}
          </Button>
          <Button variant="outline" onClick={() => onExportPdf?.(digest.id)}>
            {t('common.pdf')}
          </Button>
          <Button variant="outline" onClick={() => onExportHtml?.(digest.id)}>
            {t('common.html')}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
