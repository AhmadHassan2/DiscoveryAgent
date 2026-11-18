import { Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { DimensionScore } from "@/lib/types";

export function ScoringHelp() {
  return (
    <Tooltip>
      <TooltipTrigger className="inline-flex items-center text-muted-foreground hover:text-primary" aria-label="How scores are calculated">
        <Info className="size-3.5" />
      </TooltipTrigger>
      <TooltipContent className="max-w-xs text-xs leading-relaxed">
        Ranking heuristic, not a probability. Five dimensions are weighted: objective 35%, capabilities 30%, scope 15%, users 10%,
        technology 10%. Strong categories require both the objective and the capabilities to align, so shared keywords alone never produce a duplicate.
      </TooltipContent>
    </Tooltip>
  );
}

export function ScoreBars({ dimensions }: { dimensions: DimensionScore[] }) {
  return (
    <div className="space-y-2">
      {dimensions.map((d) => (
        <div key={d.name} className="grid grid-cols-[110px_1fr_36px] items-center gap-2 text-xs" title={d.explanation}>
          <span className="text-muted-foreground">{d.label}</span>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
            {d.score != null && (
              <div className="h-full rounded-full" style={{ width: `${Math.max(3, d.score * 100)}%`, background: d.score >= 0.6 ? "var(--brand-navy)" : d.score >= 0.35 ? "#5b8def" : "#cbd5e1" }} />
            )}
          </div>
          <span className="text-right font-mono tabular-nums">{d.score == null ? "n/a" : Math.round(d.score * 100)}</span>
        </div>
      ))}
    </div>
  );
}
