import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { intelligenceApi } from "@/lib/api/intelligence";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Clock, Users, FileText } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { UrgencyBadge } from "./components/urgency-badge";
import { EntityChip } from "./components/entity-chip";
import { PatientZero } from "./components/patient-zero";

export function ClusterDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: cluster, isLoading } = useQuery({
    queryKey: ["intelligence", "cluster", id],
    queryFn: () => intelligenceApi.getClusterDetail(id!),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-8 text-center text-slate-500">Chargement du narratif...</div>;
  if (!cluster) return <div className="p-8 text-center text-slate-500">Narratif introuvable.</div>;

  return (
    <div className="container mx-auto p-6 max-w-5xl space-y-8">
      <Link to="/intelligence">
        <Button variant="ghost" className="pl-0 gap-2 mb-4">
          <ArrowLeft className="h-4 w-4" />
          Retour à la Situation Room
        </Button>
      </Link>

      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Badge variant="outline">Cluster {cluster.id.slice(0, 8)}</Badge>
              <span className="text-sm text-slate-500">
                Mis à jour {formatDistanceToNow(new Date(cluster.updated_at), { addSuffix: true })}
              </span>
            </div>
            <h1 className="text-3xl font-bold text-slate-900">{cluster.title || "Sujet Émergent"}</h1>
          </div>
          <UrgencyBadge score={cluster.urgency_score || 0} className="text-sm px-3 py-1" />
        </div>

        {cluster.structured_summary ? (
          <div className="bg-white border-l-4 border-blue-600 shadow-sm rounded-r-lg p-6 space-y-4">
            <h2 className="text-xl font-bold text-slate-900">{cluster.structured_summary.headline}</h2>
            
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Points Clés</h3>
              <ul className="list-disc list-inside space-y-1 text-slate-800">
                {cluster.structured_summary.bullets.map((point, i) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </div>
            
            <div className="pt-2">
              <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-1">Contexte</h3>
              <p className="text-slate-700 italic">{cluster.structured_summary.context}</p>
            </div>
          </div>
        ) : (
          <p className="text-lg text-slate-700 leading-relaxed border-l-4 border-blue-500 pl-4 py-1 bg-blue-50/50 rounded-r">
            {cluster.summary || "Ce narratif est en cours d'analyse. Aucun résumé généré pour le moment."}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="space-y-6">
          <Card className="p-4 bg-slate-50 border-slate-200">
            <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Users className="h-4 w-4" />
              Entités Impliquées
            </h3>
            <div className="flex flex-wrap">
              {cluster.entities.length > 0 ? (
                cluster.entities.map(e => <EntityChip key={e.id} entity={e} />)
              ) : (
                <span className="text-sm text-slate-400 italic">Aucune entité détectée</span>
              )}
            </div>
          </Card>

          {(cluster.velocity || 0) > 0 && (
            <Card className="p-4 bg-slate-50 border-slate-200">
              <h3 className="font-semibold text-slate-900 mb-2 flex items-center gap-2">
                <Clock className="h-4 w-4 text-orange-500" />
                Dynamique
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Vélocité</span>
                  <span className="font-medium">{(cluster.velocity || 0).toFixed(1)} msg/h</span>
                </div>
                {(cluster.emergence_score || 0) > 5 && (
                  <Badge className="w-full justify-center bg-purple-600 hover:bg-purple-700">
                    Sujet Émergent 🔥
                  </Badge>
                )}
              </div>
            </Card>
          )}

          <PatientZero 
            channelId={cluster.primary_source_channel_id} 
            firstSeenAt={cluster.first_message_at} 
          />
        </div>

        <div className="md:col-span-2 space-y-6">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Derniers Messages du Flux
          </h3>
          
          <div className="space-y-4">
            {cluster.messages_preview.map((msg) => (
              <Card key={msg.id} className="p-4 hover:bg-slate-50 transition-colors">
                <p className="text-slate-800 text-sm leading-relaxed whitespace-pre-wrap">
                  {msg.text}
                </p>
                <div className="mt-2 flex justify-end">
                  <Button variant="link" size="sm" className="h-auto p-0 text-blue-600 text-xs">
                    Voir le contexte complet &rarr;
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
