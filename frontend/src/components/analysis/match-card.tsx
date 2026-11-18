"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Boxes, ChevronDown, CircleAlert, GitCompareArrows, Mail, User } from "lucide-react";
import { CategoryBadge, FactLabel, LifecycleBadge, SourceBadge } from "@/components/app/badges";
import { EvidenceList } from "@/components/analysis/evidence";
import { ScoreBars, ScoringHelp } from "@/components/analysis/score-bars";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { InitiativeMatch } from "@/lib/types";
import { cn, relativeDays } from "@/lib/utils";

export function MatchCard({ match: m, analysisId, rank, defaultOpen = false }: { match: InitiativeMatch; analysisId: string; rank: number; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const aiExplained = m.explanation_generated_by.startsWith("llm");
  const kindLabel = m.kind === "registered_idea" ? "Registered idea" : m.kind === "unindexed" ? "Unindexed initiative" : null;

  return (
    <Collapsible open={open} onOpenChange={setOpen} asChild>
      <article className={cn("print-break overflow-hidden rounded-xl border bg-white transition-shadow", open && "shadow-md ring-1 ring-[var(--brand-blue)]/20")}>
        <CollapsibleTrigger className="flex w-full items-center gap-4 px-5 py-4 text-left hover:bg-secondary/50" aria-label={`${m.name}: ${m.category_label}. ${open ? "Hide" : "Show"} details`}>
          <span className="grid size-9 shrink-0 place-items-center rounded-full bg-secondary text-sm font-semibold text-[var(--brand-navy)]">{rank}</span>
          <span className="min-w-0 flex-1">
            <span className="flex flex-wrap items-center gap-2">
              <span className="text-lg font-semibold text-[var(--brand-navy)]">{m.name}</span>
              {kindLabel && <span className="rounded bg-secondary px-1.5 py-0.5 text-xs font-medium text-secondary-foreground">{kindLabel}</span>}
            </span>
            <span className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
              {m.department && <span>{m.department}</span>}
              {m.owner && <span className="inline-flex items-center gap-1"><User className="size-3.5" aria-hidden />{m.owner.name}</span>}
              <LifecycleBadge stage={m.lifecycle.stage} />
              <span className="hidden flex-wrap gap-1 sm:flex">{m.sources_with_evidence.map((s) => <SourceBadge key={s} source={s} />)}</span>
            </span>
          </span>
          <span className="flex shrink-0 flex-col items-end gap-1.5">
            <CategoryBadge category={m.category} />
            <span className="text-sm text-muted-foreground"><span className="font-semibold text-[var(--brand-navy)] tabular-nums">{Math.round(m.overall_score * 100)}</span>/100</span>
          </span>
          <ChevronDown className={cn("size-5 shrink-0 text-slate-500 transition-transform", open && "rotate-180")} aria-hidden />
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="grid gap-8 border-t px-5 py-6 lg:grid-cols-[1fr_300px]">
            <div className="min-w-0 space-y-6">
              <section>
                <div className="mb-2 flex items-center gap-2"><h4 className="font-semibold text-[var(--brand-navy)]">Why it matches</h4><FactLabel kind={aiExplained ? "ai" : "rule"} /></div>
                <p className="text-[15px] leading-relaxed">{m.explanation}</p>
                {m.llm_adjustment && <p className="mt-2 text-sm text-muted-foreground italic">{m.llm_adjustment}</p>}
              </section>

              <section className="overflow-hidden rounded-lg border">
                <CompareRow title="In both" items={m.shared_capabilities} strong />
                <CompareRow title="Only in your idea" items={m.idea_only_capabilities} />
                <CompareRow title={`Only in ${m.kind === "registered_idea" ? "that idea" : "this initiative"}`} items={m.initiative_only_capabilities} />
              </section>

              <section>
                <div className="mb-2 flex items-center gap-2"><h4 className="font-semibold text-[var(--brand-navy)]">Source evidence ({m.evidence.length})</h4><FactLabel kind="fact" /></div>
                <EvidenceList items={m.evidence} max={4} />
              </section>
            </div>

            <aside className="space-y-6">
              <section>
                <h4 className="mb-2 text-sm font-semibold text-[var(--brand-navy)]">Owner</h4>
                {m.owner ? (
                  <div className="space-y-1 text-sm">
                    <p className="flex items-center gap-1.5 font-medium"><User className="size-4 text-[var(--brand-blue)]" aria-hidden />{m.owner.name}</p>
                    <p className="text-muted-foreground">{m.owner.role}{m.owner.team ? ` · ${m.owner.team}` : ""}</p>
                    {m.owner.email && <a href={`mailto:${m.owner.email}`} className="inline-flex items-center gap-1 text-[var(--brand-blue)] hover:underline"><Mail className="size-3.5" aria-hidden />{m.owner.email}</a>}
                    <p className="text-xs text-muted-foreground">Source: {m.owner.provenance}</p>
                  </div>
                ) : <p className="text-sm text-muted-foreground">Unknown. No owner was found in the source records.</p>}
              </section>

              <section>
                <h4 className="mb-2 text-sm font-semibold text-[var(--brand-navy)]">Status</h4>
                <LifecycleBadge stage={m.lifecycle.stage} confidence={m.lifecycle.confidence} />
                {m.lifecycle.last_activity_at && <p className="mt-1.5 text-sm text-muted-foreground">Last activity {relativeDays(m.lifecycle.last_activity_at)}</p>}
              </section>

              <section>
                <h4 className="mb-3 flex items-center gap-1 text-sm font-semibold text-[var(--brand-navy)]">Overlap by dimension <ScoringHelp /></h4>
                <ScoreBars dimensions={m.dimensions} />
              </section>

              {m.recommendations.length > 0 && (
                <section>
                  <h4 className="mb-2 text-sm font-semibold text-[var(--brand-navy)]">Next steps</h4>
                  <ol className="space-y-3">
                    {m.recommendations.map((r, i) => (
                      <li key={r.label} className="flex gap-3 text-sm">
                        <span className="grid size-6 shrink-0 place-items-center rounded-full bg-[var(--brand-navy)] text-xs font-semibold text-white">{i + 1}</span>
                        <span><span className="block font-medium text-[var(--brand-navy)]">{r.label}</span><span className="text-muted-foreground">{r.detail}</span></span>
                      </li>
                    ))}
                  </ol>
                </section>
              )}

              {m.reusable_components.length > 0 && (
                <section>
                  <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-[var(--brand-navy)]"><Boxes className="size-4" aria-hidden />Reusable components</h4>
                  <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">{m.reusable_components.map((c) => <li key={c}>{c}</li>)}</ul>
                </section>
              )}

              {m.uncertainty.length > 0 && (
                <section className="rounded-lg bg-secondary p-3 text-sm">
                  <p className="mb-1 flex items-center gap-1.5 font-medium text-[var(--brand-navy)]"><CircleAlert className="size-4" aria-hidden />Uncertainty</p>
                  <ul className="space-y-1 text-muted-foreground">{m.uncertainty.map((u) => <li key={u}>{u}</li>)}</ul>
                </section>
              )}

              {m.related_initiatives.length > 0 && (
                <section className="text-sm">
                  <h4 className="mb-1 font-semibold text-[var(--brand-navy)]">Related</h4>
                  <ul className="space-y-1 text-muted-foreground">{m.related_initiatives.map((r) => <li key={r.id}><span className="font-medium text-foreground">{r.name}</span>: {r.reason}</li>)}</ul>
                </section>
              )}

              <div className="no-print flex flex-col gap-2">
                <Button asChild className="h-11">
                  <Link href={`/analysis/${analysisId}/compare/${encodeURIComponent(m.initiative_id)}`}><GitCompareArrows className="size-4" aria-hidden />Compare side by side</Link>
                </Button>
                {m.kind === "initiative" && (
                  <Button asChild variant="outline" className="h-11">
                    <Link href={`/projects/${m.initiative_id}`}>View initiative <ArrowRight className="size-4" aria-hidden /></Link>
                  </Button>
                )}
              </div>
            </aside>
          </div>
        </CollapsibleContent>
      </article>
    </Collapsible>
  );
}

function CompareRow({ title, items, strong }: { title: string; items: string[]; strong?: boolean }) {
  return (
    <div className="grid border-b last:border-b-0 sm:grid-cols-[160px_1fr]">
      <div className={cn("px-4 py-3 text-sm font-medium", strong ? "bg-[var(--brand-navy)] text-white" : "bg-secondary text-[var(--brand-navy)]")}>{title}</div>
      <div className="px-4 py-3 text-sm">
        {items.length ? <ul className="space-y-1">{items.map((i) => <li key={i}>{i}</li>)}</ul> : <span className="text-muted-foreground">Nothing identified</span>}
      </div>
    </div>
  );
}
