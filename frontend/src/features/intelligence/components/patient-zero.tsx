import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatDistanceToNow } from "date-fns";

interface PatientZeroProps {
  channelId?: string;
  firstSeenAt?: string;
}

export function PatientZero({ channelId, firstSeenAt }: PatientZeroProps) {
  if (!channelId) return null;

  return (
    <Card className="p-3 bg-slate-50 border-slate-200">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Source Primaire (Patient Zero)</h4>
          <p className="font-medium text-sm mt-1">Channel ID: {channelId.slice(0, 8)}...</p>
        </div>
        {firstSeenAt && (
          <Badge variant="outline" className="text-xs">
            {formatDistanceToNow(new Date(firstSeenAt), { addSuffix: true })}
          </Badge>
        )}
      </div>
    </Card>
  );
}
