import { cn } from "@/lib/cn";

interface UrgencyBadgeProps {
  score: number;
  className?: string;
}

export function UrgencyBadge({ score, className }: UrgencyBadgeProps) {
  const getColor = (score: number) => {
    if (score >= 8) return "bg-red-500 text-white animate-pulse";
    if (score >= 5) return "bg-orange-500 text-white";
    if (score >= 3) return "bg-yellow-500 text-white";
    return "bg-slate-500 text-white";
  };

  return (
    <span className={cn("px-2 py-1 rounded text-xs font-bold", getColor(score), className)}>
      TENSION: {score}/10
    </span>
  );
}
