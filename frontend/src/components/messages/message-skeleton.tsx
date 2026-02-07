interface MessageSkeletonProps {
  count?: number
}

function SingleSkeleton() {
  return (
    <div className="animate-shimmer relative rounded-xl border border-border bg-card shadow-sm overflow-hidden">
      {/* Channel accent bar */}
      <div className="absolute left-0 top-0 h-full w-1 bg-muted" />
      <div className="flex flex-col gap-4 py-6 pl-6 pr-5">
        {/* Header row */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="h-4 w-24 rounded bg-muted" />
          <div className="h-4 w-16 rounded bg-muted" />
          <div className="h-4 w-20 rounded bg-muted" />
          <div className="h-5 w-8 rounded-full bg-muted" />
          <div className="h-5 w-16 rounded-full bg-muted" />
          <div className="h-5 w-20 rounded-full bg-muted" />
        </div>

        {/* Content */}
        <div className="space-y-2">
          <div className="h-4 w-full rounded bg-muted" />
          <div className="h-4 w-5/6 rounded bg-muted" />
          <div className="h-4 w-4/6 rounded bg-muted" />
        </div>

        {/* Original text box */}
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
      </div>
    </div>
  )
}

export function MessageSkeleton({ count = 5 }: MessageSkeletonProps) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} style={{ animationDelay: `${index * 100}ms` }}>
          <SingleSkeleton />
        </div>
      ))}
    </div>
  )
}
