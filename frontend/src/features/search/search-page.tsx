import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { MessageFeed } from '@/components/messages/message-feed'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { messagesApi } from '@/lib/api/client'

export function SearchPage() {
  const [query, setQuery] = useState('')

  const searchQuery = useQuery({
    queryKey: ['search', query],
    queryFn: async () => (await messagesApi.list({ limit: 20, offset: 0 })).data,
    enabled: query.length > 2,
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-sm text-foreground/60">Rechercher dans les signaux</p>
        <h2 className="text-2xl font-semibold">Recherche</h2>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Input
          placeholder="Rechercher un sujet, une entite, un canal..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <Button variant="secondary">Lancer</Button>
      </div>

      <Tabs defaultValue="semantic">
        <TabsList>
          <TabsTrigger value="semantic">Semantique</TabsTrigger>
          <TabsTrigger value="keyword">Mot-cle</TabsTrigger>
          <TabsTrigger value="entities">Entites</TabsTrigger>
        </TabsList>
        <TabsContent value="semantic">
          {query.length < 3 ? (
            <Card>
              <CardContent className="py-10 text-sm text-foreground/60">
                Tapez au moins 3 caracteres pour lancer la recherche.
              </CardContent>
            </Card>
          ) : (
            <MessageFeed messages={searchQuery.data?.messages ?? []} isLoading={searchQuery.isLoading} />
          )}
        </TabsContent>
        <TabsContent value="keyword">
          <Card>
            <CardContent className="py-10 text-sm text-foreground/60">
              Recherche par mot-cle (bientot).
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="entities">
          <Card>
            <CardContent className="py-10 text-sm text-foreground/60">
              Filtrer par entites extraites.
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
