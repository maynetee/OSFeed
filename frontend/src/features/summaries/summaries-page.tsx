import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { format } from 'date-fns'
import { Sparkles, Trash2 } from 'lucide-react'

import { PageTransition } from '@/components/layout/page-transition'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { summariesApi } from '@/lib/api/summaries'
import type { SummaryResponse } from '@/lib/api/summaries'
import { SummaryDisplay } from './summary-display'

export function SummariesPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [selectedSummary, setSelectedSummary] = useState<SummaryResponse | null>(null)

  const summariesQuery = useQuery({
    queryKey: ['summaries'],
    queryFn: async () => (await summariesApi.list({ limit: 50 })).data,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => summariesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['summaries'] })
      setSelectedSummary(null)
    },
  })

  const summaries = summariesQuery.data?.summaries ?? []

  return (
    <PageTransition>
      <div className="flex flex-col gap-6">
        <div>
          <p className="text-sm text-foreground/60">{t('summaries.subtitle')}</p>
          <h2 className="text-2xl font-semibold">{t('summaries.title')}</h2>
        </div>

        {selectedSummary ? (
          <div className="flex flex-col gap-4">
            <Button
              variant="outline"
              size="sm"
              className="w-fit"
              onClick={() => setSelectedSummary(null)}
            >
              {t('summaries.backToSummaries')}
            </Button>
            <Card>
              <CardContent className="py-6">
                <SummaryDisplay summary={selectedSummary} />
                <div className="mt-4 border-t border-border/50 pt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 text-danger"
                    onClick={() => deleteMutation.mutate(selectedSummary.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    {t('summaries.deleteSummary')}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : summaries.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-12">
              <Sparkles className="h-8 w-8 text-foreground/30" />
              <p className="text-sm text-foreground/60">{t('summaries.empty')}</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {summaries.map((summary) => (
              <Card
                key={summary.id}
                className="cursor-pointer transition-colors hover:bg-muted/30"
                onClick={() => setSelectedSummary(summary)}
              >
                <CardContent className="flex flex-col gap-3 py-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-foreground/50">
                      {format(new Date(summary.created_at), 'PPp')}
                    </span>
                    <Badge variant="muted">{summary.message_count} msgs</Badge>
                  </div>
                  <p className="line-clamp-3 text-sm text-foreground/80">{summary.summary_text}</p>
                  {summary.key_themes.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {summary.key_themes.slice(0, 3).map((theme, i) => (
                        <Badge key={i} variant="default" className="text-[10px]">
                          {theme}
                        </Badge>
                      ))}
                      {summary.key_themes.length > 3 && (
                        <Badge variant="muted" className="text-[10px]">
                          +{summary.key_themes.length - 3}
                        </Badge>
                      )}
                    </div>
                  )}
                  <Button variant="outline" size="sm" className="mt-auto w-fit">
                    {t('summaries.viewSummary')}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </PageTransition>
  )
}
