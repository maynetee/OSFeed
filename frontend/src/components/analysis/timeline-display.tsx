import { useTranslation } from 'react-i18next'
import type { TimelineEvent } from '@/lib/api/analysis'
import { Badge } from '@/components/ui/badge'

function SignificanceDots({ level }: { level: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className={`h-2 w-2 rounded-full ${i < level ? 'bg-primary' : 'bg-muted'}`} />
      ))}
    </div>
  )
}

interface TimelineDisplayProps {
  events: TimelineEvent[]
}

export function TimelineDisplay({ events }: TimelineDisplayProps) {
  const { t } = useTranslation()

  if (!events.length) {
    return (
      <p className="text-sm text-foreground-muted py-8 text-center">
        {t('analysis.timeline.noTimelines')}
      </p>
    )
  }

  return (
    <div className="relative ml-4">
      {/* Vertical line */}
      <div className="absolute left-0 top-0 bottom-0 w-px bg-border" />

      <div className="space-y-6">
        {events.map((event, index) => (
          <div key={index} className="relative pl-8">
            {/* Dot on the line */}
            <div className="absolute left-0 top-1 -translate-x-1/2 h-3 w-3 rounded-full border-2 border-primary bg-background" />

            <div className="space-y-1.5">
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-foreground-muted">{event.date}</span>
                <SignificanceDots level={event.significance} />
              </div>

              <p className="text-sm text-foreground">{event.description}</p>

              {event.sources.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {event.sources.map((source) => (
                    <Badge key={source} variant="muted" className="text-xs">
                      {source}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
