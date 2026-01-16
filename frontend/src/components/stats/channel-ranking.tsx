import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

interface ChannelRankingProps {
  data: { channel_title: string; count: number }[]
}

export function ChannelRanking({ data }: ChannelRankingProps) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 py-6">
        <p className="text-sm font-semibold">Top canaux</p>
        <div className="space-y-3">
          {data.map((channel) => (
            <div key={channel.channel_title} className="flex items-center justify-between text-sm">
              <span>{channel.channel_title}</span>
              <Badge variant="outline">{channel.count}</Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
