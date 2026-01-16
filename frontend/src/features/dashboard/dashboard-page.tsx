import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { KpiCard } from '@/components/stats/kpi-card'
import { TrendChart } from '@/components/stats/trend-chart'
import { ChannelRanking } from '@/components/stats/channel-ranking'
import { statsApi } from '@/lib/api/client'

export function DashboardPage() {
  const overviewQuery = useQuery({
    queryKey: ['stats-overview'],
    queryFn: async () => (await statsApi.overview()).data,
  })

  const messagesByDayQuery = useQuery({
    queryKey: ['stats-messages-by-day'],
    queryFn: async () => (await statsApi.messagesByDay(7)).data,
  })

  const messagesByChannelQuery = useQuery({
    queryKey: ['stats-messages-by-channel'],
    queryFn: async () => (await statsApi.messagesByChannel(5)).data,
  })

  const overview = overviewQuery.data

  return (
    <div className="flex flex-col gap-8">
      <section className="grid gap-4 md:grid-cols-3">
        <KpiCard
          label="Messages aujourd'hui"
          value={overview ? overview.messages_last_24h.toLocaleString() : '--'}
          delta="+23%"
          trend="up"
        />
        <KpiCard
          label="Duplicatas filtres"
          value={overview ? `${Math.round((overview.duplicates_last_24h / (overview.messages_last_24h || 1)) * 100)}%` : '--'}
          delta="-4%"
          trend="down"
        />
        <KpiCard
          label="Canaux actifs"
          value={overview ? overview.active_channels.toLocaleString() : '--'}
          delta="+11%"
          trend="up"
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card className="overflow-hidden">
          <CardHeader className="flex items-start justify-between gap-4 md:flex-row md:items-center">
            <div>
              <CardTitle>Daily Digest</CardTitle>
              <p className="text-sm text-foreground/60">
                3 evenements majeurs, synthese en 3 minutes.
              </p>
            </div>
            <Button variant="outline">Voir digest complet</Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {['Tensions en mer Noire', 'Nouvelles sanctions economiques', 'Mobilisation logistique'].map(
              (item) => (
                <div key={item} className="flex items-start justify-between gap-4 rounded-lg bg-muted/40 p-4">
                  <div>
                    <p className="text-sm font-semibold">{item}</p>
                    <p className="text-xs text-foreground/60">12 sources recoupees, 2 heures</p>
                  </div>
                  <Badge variant="outline">Signal fort</Badge>
                </div>
              ),
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Confiance</CardTitle>
            <p className="text-sm text-foreground/60">Indicateurs de fiabilite.</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span>Sources primaires</span>
              <span className="font-semibold">68%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Risque propagande</span>
              <span className="font-semibold text-warning">12%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Canaux verifies</span>
              <span className="font-semibold">31</span>
            </div>
            <Button className="w-full" variant="secondary">
              Ouvrir tableau de bord
            </Button>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Activite sur 7 jours</CardTitle>
            <p className="text-sm text-foreground/60">Volume de messages collectes.</p>
          </CardHeader>
          <CardContent>
            <TrendChart data={messagesByDayQuery.data ?? []} />
          </CardContent>
        </Card>
        <ChannelRanking data={messagesByChannelQuery.data ?? []} />
      </section>
    </div>
  )
}
