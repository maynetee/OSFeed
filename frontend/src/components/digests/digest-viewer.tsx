import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { EntityTags } from '@/components/digests/entity-tags'
import type { Summary } from '@/lib/api/client'

interface DigestViewerProps {
  digest?: Summary
  isLoading?: boolean
}

export function DigestViewer({ digest, isLoading }: DigestViewerProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-10 text-sm text-foreground/60">Chargement du digest...</CardContent>
      </Card>
    )
  }

  if (!digest) {
    return (
      <Card>
        <CardContent className="py-10 text-sm text-foreground/60">Aucun digest disponible.</CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{digest.title ?? 'Daily Digest'}</CardTitle>
          <p className="text-sm text-foreground/60">
            {digest.message_count} messages · {digest.channels_covered ?? 0} canaux
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm leading-relaxed text-foreground/80">{digest.content}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Entites</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6 md:grid-cols-3">
          <EntityTags label="Personnes" entities={digest.entities?.persons} />
          <EntityTags label="Lieux" entities={digest.entities?.locations} />
          <EntityTags label="Organisations" entities={digest.entities?.organizations} />
        </CardContent>
      </Card>
    </div>
  )
}
