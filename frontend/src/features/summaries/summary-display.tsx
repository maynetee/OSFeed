import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Check, ClipboardCopy, Download } from 'lucide-react'
import { format } from 'date-fns'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { SummaryResponse } from '@/lib/api/summaries'

interface SummaryDisplayProps {
  summary: SummaryResponse
}

export function SummaryDisplay({ summary }: SummaryDisplayProps) {
  const { t } = useTranslation()
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    const text = [
      `# ${t('summaries.executiveSummary')}`,
      summary.summary_text,
      '',
      `## ${t('summaries.keyThemes')}`,
      ...summary.key_themes.map((theme) => `- ${theme}`),
      '',
      `## ${t('summaries.notableEvents')}`,
      ...summary.notable_events.map((event) => `- ${event}`),
    ].join('\n')
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const downloadMarkdown = () => {
    const text = [
      `# Intelligence Summary`,
      `*${format(new Date(summary.date_range_start), 'PP')} - ${format(new Date(summary.date_range_end), 'PP')}*`,
      `*${t('summaries.messageCount', { count: summary.message_count })}*`,
      '',
      `## Executive Summary`,
      summary.summary_text,
      '',
      `## Key Themes`,
      ...summary.key_themes.map((theme) => `- ${theme}`),
      '',
      `## Notable Events`,
      ...summary.notable_events.map((event) => `- ${event}`),
    ].join('\n')
    const blob = new Blob([text], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `summary-${format(new Date(summary.created_at), 'yyyy-MM-dd')}.md`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Executive Summary */}
      <div>
        <h4 className="mb-2 text-sm font-semibold text-foreground/80">
          {t('summaries.executiveSummary')}
        </h4>
        <p className="text-sm leading-relaxed text-foreground/90">{summary.summary_text}</p>
      </div>

      {/* Key Themes */}
      {summary.key_themes.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-foreground/80">
            {t('summaries.keyThemes')}
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {summary.key_themes.map((theme, i) => (
              <Badge key={i} variant="default">
                {theme}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Notable Events */}
      {summary.notable_events.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-foreground/80">
            {t('summaries.notableEvents')}
          </h4>
          <ul className="list-inside list-disc space-y-1 text-sm text-foreground/80">
            {summary.notable_events.map((event, i) => (
              <li key={i}>{event}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Metadata */}
      <div className="flex flex-wrap items-center gap-3 border-t border-border/50 pt-3 text-xs text-foreground/50">
        <span>{t('summaries.messageCount', { count: summary.message_count })}</span>
        {summary.model_used && (
          <span>{t('summaries.modelUsed', { model: summary.model_used })}</span>
        )}
        {summary.generation_time_seconds != null && (
          <span>
            {t('summaries.generationTime', {
              seconds: summary.generation_time_seconds.toFixed(1),
            })}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button variant="outline" size="sm" className="gap-1.5" onClick={copyToClipboard}>
          {copied ? <Check className="h-3.5 w-3.5" /> : <ClipboardCopy className="h-3.5 w-3.5" />}
          {copied ? t('summaries.copied') : t('summaries.copyToClipboard')}
        </Button>
        <Button variant="outline" size="sm" className="gap-1.5" onClick={downloadMarkdown}>
          <Download className="h-3.5 w-3.5" />
          {t('summaries.downloadMarkdown')}
        </Button>
      </div>
    </div>
  )
}
