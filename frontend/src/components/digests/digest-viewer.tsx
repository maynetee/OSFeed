import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { EntityTags } from '@/components/digests/entity-tags'
import type { Summary } from '@/lib/api/client'
import { useTranslation } from 'react-i18next'

interface DigestViewerProps {
  digest?: Summary
  isLoading?: boolean
}

export function DigestViewer({ digest, isLoading }: DigestViewerProps) {
  const { t } = useTranslation()

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-10 text-sm text-foreground/60">
          {t('digestViewer.loading')}
        </CardContent>
      </Card>
    )
  }

  if (!digest) {
    return (
      <Card>
        <CardContent className="py-10 text-sm text-foreground/60">
          {t('digestViewer.empty')}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{digest.title ?? t('digests.title')}</CardTitle>
          <p className="text-sm text-foreground/60">
            {digest.message_count} messages · {t('digestViewer.channels', { count: digest.channels_covered ?? 0 })}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm leading-relaxed text-foreground/80">{digest.content}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('digestViewer.entities')}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6 md:grid-cols-3">
          <EntityTags label={t('messages.entitiesPeople')} entities={digest.entities?.persons} />
          <EntityTags label={t('messages.entitiesLocations')} entities={digest.entities?.locations} />
          <EntityTags label={t('messages.entitiesOrganizations')} entities={digest.entities?.organizations} />
        </CardContent>
      </Card>
    </div>
  )
}
