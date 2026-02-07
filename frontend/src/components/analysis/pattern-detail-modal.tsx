import { useTranslation } from 'react-i18next'

import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import type { DetectedPatternResponse } from '@/lib/api/analysis'

const PATTERN_TYPE_STYLES: Record<string, string> = {
  volume_spike: 'bg-amber-500/10 text-amber-400',
  narrative_shift: 'bg-purple-500/10 text-purple-400',
  entity_emergence: 'bg-blue-500/10 text-blue-400',
}

const PATTERN_TYPE_KEYS: Record<string, string> = {
  volume_spike: 'analysis.patterns.volumeSpike',
  narrative_shift: 'analysis.patterns.narrativeShift',
  entity_emergence: 'analysis.patterns.entityEmergence',
}

interface PatternDetailModalProps {
  pattern: DetectedPatternResponse | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function PatternDetailModal({ pattern, open, onOpenChange }: PatternDetailModalProps) {
  const { t } = useTranslation()

  if (!pattern) return null

  const confidencePct = Math.round(pattern.confidence * 100)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Badge
              className={PATTERN_TYPE_STYLES[pattern.pattern_type] ?? 'bg-muted text-foreground/60'}
            >
              {t(PATTERN_TYPE_KEYS[pattern.pattern_type] ?? pattern.pattern_type)}
            </Badge>
            <DialogTitle>{pattern.title}</DialogTitle>
          </div>
          <DialogDescription>
            {new Date(pattern.detected_at).toLocaleString()}
          </DialogDescription>
        </DialogHeader>

        <div className="mt-4 space-y-4">
          {pattern.description && (
            <p className="text-sm text-foreground/80">{pattern.description}</p>
          )}

          <div className="space-y-1">
            <p className="text-xs font-medium text-foreground/60">
              {t('analysis.patterns.confidence')}
            </p>
            <div className="flex items-center gap-3">
              <div className="h-2 flex-1 rounded-full bg-muted">
                <div
                  className="h-2 rounded-full bg-primary transition-all"
                  style={{ width: `${confidencePct}%` }}
                />
              </div>
              <span className="text-sm font-semibold tabular-nums">{confidencePct}%</span>
            </div>
          </div>

          {pattern.evidence_message_ids.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-foreground/60">
                {t('analysis.patterns.evidence')}
              </p>
              <div className="flex flex-wrap gap-1">
                {pattern.evidence_message_ids.map((id) => (
                  <span
                    key={id}
                    className="rounded bg-muted px-2 py-0.5 text-xs font-mono text-foreground/60"
                  >
                    {id.slice(0, 8)}...
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
