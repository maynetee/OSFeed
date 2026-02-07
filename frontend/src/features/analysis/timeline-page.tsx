import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2 } from 'lucide-react'

import { PageTransition } from '@/components/layout/page-transition'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TimelineDisplay } from '@/components/analysis/timeline-display'
import { TimelineGenerateModal } from '@/features/analysis/timeline-generate-modal'
import { analysisApi } from '@/lib/api/analysis'
import type { TimelineResponse } from '@/lib/api/analysis'

export function TimelinePage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [generateOpen, setGenerateOpen] = useState(false)
  const [selectedTimeline, setSelectedTimeline] = useState<TimelineResponse | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['timelines'],
    queryFn: async () => (await analysisApi.listTimelines()).data,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => analysisApi.deleteTimeline(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timelines'] })
      setSelectedTimeline(null)
    },
  })

  const timelines = data?.timelines ?? []

  if (selectedTimeline) {
    return (
      <PageTransition>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={() => setSelectedTimeline(null)}
                className="text-sm text-foreground-muted hover:text-foreground mb-2"
              >
                &larr; {t('analysis.timeline.myTimelines')}
              </button>
              <h1 className="text-2xl font-semibold">{selectedTimeline.title}</h1>
              <div className="flex items-center gap-3 mt-1">
                {selectedTimeline.topic && (
                  <Badge variant="default">{selectedTimeline.topic}</Badge>
                )}
                <span className="text-sm text-foreground-muted">
                  {t('analysis.timeline.events', { count: selectedTimeline.events.length })}
                </span>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (confirm(t('analysis.timeline.deleteConfirm'))) {
                  deleteMutation.mutate(selectedTimeline.id)
                }
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>

          <Card>
            <CardContent className="pt-6">
              <TimelineDisplay events={selectedTimeline.events} />
            </CardContent>
          </Card>
        </div>
      </PageTransition>
    )
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">{t('analysis.timeline.title')}</h1>
          <Button onClick={() => setGenerateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            {t('analysis.timeline.generate')}
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 animate-pulse rounded-xl bg-muted" />
            ))}
          </div>
        ) : timelines.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-foreground-muted">{t('analysis.timeline.noTimelines')}</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {timelines.map((timeline) => (
              <Card
                key={timeline.id}
                className="cursor-pointer transition-colors hover:border-primary/30"
                onClick={() => setSelectedTimeline(timeline)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{timeline.title}</CardTitle>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm(t('analysis.timeline.deleteConfirm'))) {
                          deleteMutation.mutate(timeline.id)
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center gap-3 text-sm text-foreground-muted">
                    {timeline.topic && <Badge variant="default">{timeline.topic}</Badge>}
                    <span>{t('analysis.timeline.events', { count: timeline.events.length })}</span>
                    <span>{new Date(timeline.created_at).toLocaleDateString()}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <TimelineGenerateModal open={generateOpen} onOpenChange={setGenerateOpen} />
      </div>
    </PageTransition>
  )
}
