import { EntityRef } from "@/types/intelligence";
import { cn } from "@/lib/cn";

interface EntityChipProps {
  entity: EntityRef;
}

export function EntityChip({ entity }: EntityChipProps) {
  const colors = {
    ORG: "bg-blue-100 text-blue-800 border-blue-200",
    LOC: "bg-emerald-100 text-emerald-800 border-emerald-200",
    PER: "bg-purple-100 text-purple-800 border-purple-200",
    MISC: "bg-gray-100 text-gray-800 border-gray-200",
  };

  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border mr-1 mb-1", colors[entity.type] || colors.MISC)}>
      {entity.name}
      <span className="ml-1 text-[10px] opacity-60">({entity.frequency})</span>
    </span>
  );
}
