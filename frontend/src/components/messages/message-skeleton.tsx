import { Card, CardContent } from '@/components/ui/card'

interface MessageSkeletonProps {
  count?: number
}

function SingleSkeleton() {
  return (
    <Card className="animate-pulse">
      <CardContent className="flex flex-col gap-4 py-6">
        {/* Header row */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="h-4 w-24 rounded bg-muted" />
            <div className="h-4 w-16 rounded bg-muted" />
            <div className="h-4 w-20 rounded bg-muted" />
            <div className="h-5 w-8 rounded-full bg-muted" />
          </div>
          <div className="flex items-center gap-2">
            <div className="h-5 w-16 rounded-full bg-muted" />
            <div className="h-5 w-20 rounded-full bg-muted" />
          </div>
        </div>

        {/* Content */}
        <div className="space-y-2">
          <div className="h-4 w-full rounded bg-muted" />
          <div className="h-4 w-5/6 rounded bg-muted" />
          <div className="h-4 w-4/6 rounded bg-muted" />
        </div>

        {/* Original text box (occasionally visible) */}
        <div className="rounded-lg border border-border/60 bg-muted/40 p-3">
          <div className="h-3 w-16 rounded bg-muted" />
          <div className="mt-2 space-y-1.5">
            <div className="h-3 w-full rounded bg-muted/60" />
            <div className="h-3 w-3/4 rounded bg-muted/60" />
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <div className="h-8 w-24 rounded bg-muted" />
          <div className="h-8 w-16 rounded bg-muted" />
          <div className="h-8 w-20 rounded bg-muted" />
        </div>
      </CardContent>
    </Card>
  )
}

export function MessageSkeleton({ count = 5 }: MessageSkeletonProps) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, index) => (
        <SingleSkeleton key={index} />
      ))}
    </div>
  )
}
