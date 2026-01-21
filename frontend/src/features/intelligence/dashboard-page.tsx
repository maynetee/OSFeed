import { useQuery } from "@tanstack/react-query";
import { intelligenceApi } from "@/lib/api/intelligence";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import { UrgencyBadge } from "./components/urgency-badge";
import { EntityChip } from "./components/entity-chip";
import { Activity, Globe, Zap } from "lucide-react";

export function IntelligenceDashboardPage() {
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["intelligence", "dashboard"],
    queryFn: intelligenceApi.getDashboard,
    refetchInterval: 30000, 
  });

  if (isLoading) return <div className="p-8 text-center text-slate-500">Chargement de la Situation Room...</div>;
  if (!dashboard) return null;

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Globe className="h-8 w-8 text-blue-600" />
            Situation Room
          </h1>
          <p className="text-slate-500 mt-1">Surveillance temps réel des narratifs géopolitiques</p>
        </div>
        <div className="flex items-center gap-4">
          <Card className="px-4 py-2 flex items-center gap-2 bg-slate-50 border-slate-200">
            <Activity className="h-4 w-4 text-slate-500" />
            <span className="text-sm font-medium text-slate-600">Tension Globale</span>
            <Badge variant={dashboard.global_tension > 5 ? "destructive" : "secondary"}>
              {dashboard.global_tension}/10
            </Badge>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="h-5 w-5 text-orange-500" />
            <h2 className="text-xl font-semibold">Hot Topics</h2>
          </div>
          
          <div className="space-y-4">
            {dashboard.hot_topics.map((cluster) => (
              <Link to={`/intelligence/clusters/${cluster.id}`} key={cluster.id}>
                <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-transparent hover:border-l-blue-500">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-lg text-slate-800">{cluster.title || "Sujet Émergent"}</h3>
                    <div className="flex gap-2">
                      {(cluster.emergence_score || 0) > 5 && (
                        <Badge className="bg-purple-600 hover:bg-purple-700 text-xs">🔥</Badge>
                      )}
                      <UrgencyBadge score={cluster.urgency_score || 0} />
                    </div>
                  </div>
                  <p className="text-slate-600 text-sm line-clamp-2 mb-3">
                    {cluster.summary || "Pas de résumé disponible pour ce cluster..."}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span>{cluster.message_count} messages</span>
                    <span>•</span>
                    <span>Mis à jour {formatDistanceToNow(new Date(cluster.updated_at), { addSuffix: true })}</span>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="h-5 w-5 text-emerald-500" />
            <h2 className="text-xl font-semibold">Acteurs Clés</h2>
          </div>

          <Card className="p-4">
            <h3 className="text-sm font-semibold text-slate-500 mb-3 uppercase">Organisations</h3>
            <div className="flex flex-wrap">
              {dashboard.top_entities.ORG?.map(e => <EntityChip key={e.id} entity={e} />)}
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="text-sm font-semibold text-slate-500 mb-3 uppercase">Lieux</h3>
            <div className="flex flex-wrap">
              {dashboard.top_entities.LOC?.map(e => <EntityChip key={e.id} entity={e} />)}
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="text-sm font-semibold text-slate-500 mb-3 uppercase">Personnalités</h3>
            <div className="flex flex-wrap">
              {dashboard.top_entities.PER?.map(e => <EntityChip key={e.id} entity={e} />)}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
