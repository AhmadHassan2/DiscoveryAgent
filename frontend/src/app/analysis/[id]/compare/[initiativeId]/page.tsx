"use client";

import { use, useEffect, useState } from "react";
import { Boxes, CircleCheck, Lightbulb, Minus, Plus } from "lucide-react";
import { Breadcrumbs, ErrorState, PageHeader } from "@/components/app/app-shell";
import { CategoryBadge, FactLabel, LifecycleBadge } from "@/components/app/badges";
import { EvidenceList } from "@/components/analysis/evidence";
import { ScoreBars, ScoringHelp } from "@/components/analysis/score-bars";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { Comparison } from "@/lib/types";
import { relativeDays } from "@/lib/utils";

export default function ComparePage({ params }: { params: Promise<{ id: string; initiativeId: string }> }) {
  const { id, initiativeId } = use(params);
  const [data, setData] = useState<Comparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.comparison(id, decodeURIComponent(initiativeId)).then(setData).catch((e) => setError(e.message));
  }, [id, initiativeId]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <Skeleton className="h-96 w-full" />;
  const m = data.initiative;
  const ai = m.explanation_generated_by.startsWith("llm");

  return (
    <>
      <Breadcrumbs items={[{ label: "Search history", href: "/history" }, { label: data.idea.title || "Results", href: `/analysis/${id}` }, { label: `Compare with ${m.name}` }]} />
      <PageHeader eyebrow="Detailed comparison" title={`Your idea vs ${m.name}`} actions={<CategoryBadge category={m.category} size="lg" />} />

      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="Your idea" tag={<span className="rounded bg-[var(--brand-navy)] px-2 py-0.5 text-xs font-semibold text-white">Proposed</span>} accent="navy">
          <p className="text-sm leading-relaxed">{data.idea.description}</p>
        </Panel>
        <Panel title={m.name} tag={<LifecycleBadge stage={m.lifecycle.stage} confidence={m.lifecycle.confidence} />} accent="blue">
          <p className="text-sm leading-relaxed">{m.description}</p>
          <p className="mt-2 text-xs text-muted-foreground">
            {m.department}{m.team ? ` · ${m.team}` : ""}{m.owner ? ` · Owner: ${m.owner.name} (${m.owner.provenance})` : ""}
            {m.lifecycle.last_activity_at ? ` · last activity ${relativeDays(m.lifecycle.last_activity_at)}` : ""}
          </p>
        </Panel>
      </div>

      <section className="mt-6 overflow-hidden rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-muted text-left text-xs text-muted-foreground uppercase">
            <tr><th className="w-40 px-4 py-2">Aspect</th><th className="px-4 py-2">Your idea</th><th className="px-4 py-2">{m.name}</th></tr>
          </thead>
          <tbody className="divide-y">
            {data.rows.map((r) => (
              <tr key={r.aspect} className="align-top">
                <th className="px-4 py-3 text-left font-medium text-[var(--brand-navy)]">{r.aspect}</th>
                <td className="px-4 py-3">{r.idea}</td>
                <td className="px-4 py-3">{r.initiative}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <ListPanel icon={CircleCheck} title="Shared functionality" items={data.shared} cls="border-blue-200 bg-blue-50/60" />
        <ListPanel icon={Plus} title="Only in your idea" items={data.idea_only} cls="border-blue-200 bg-blue-50" />
        <ListPanel icon={Minus} title="Only in the existing initiative" items={data.initiative_only} cls="border-slate-200 bg-white" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <section className="rounded-lg border bg-white p-4">
            <div className="mb-2 flex items-center gap-2"><h3 className="text-sm font-semibold text-[var(--brand-navy)]">Assessment</h3><FactLabel kind={ai ? "ai" : "rule"} /></div>
            <p className="text-sm leading-relaxed">{m.explanation}</p>
          </section>
          <section>
            <div className="mb-2 flex items-center gap-2"><h3 className="text-sm font-semibold text-[var(--brand-navy)]">Existing implementation evidence</h3><FactLabel kind="fact" /></div>
            <EvidenceList items={m.evidence} />
          </section>
        </div>
        <aside className="space-y-4">
          <section className="rounded-lg border bg-white p-4">
            <h3 className="mb-3 flex items-center gap-1 text-sm font-semibold text-[var(--brand-navy)]">Overlap by dimension <ScoringHelp /></h3>
            <ScoreBars dimensions={m.dimensions} />
            <ul className="mt-3 space-y-1 text-xs text-muted-foreground">{m.dimensions.map((d) => <li key={d.name}><span className="font-medium text-foreground">{d.label}:</span> {d.explanation}</li>)}</ul>
          </section>
          <section className="rounded-lg border bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold text-[var(--brand-navy)]">Lifecycle signals</h3>
            <ul className="space-y-1 text-xs">{m.lifecycle.signals.map((s) => <li key={s}>• {s}</li>)}</ul>
            {m.lifecycle.caveats.map((c) => <p key={c} className="mt-2 rounded bg-amber-50 p-2 text-xs text-amber-900">{c}</p>)}
          </section>
          {m.reusable_components.length > 0 && (
            <section className="rounded-lg border bg-white p-4">
              <h3 className="mb-2 flex items-center gap-1 text-sm font-semibold text-[var(--brand-navy)]"><Boxes className="size-4" />Potentially reusable</h3>
              <ul className="list-disc space-y-0.5 pl-4 text-sm">{m.reusable_components.map((c) => <li key={c}>{c}</li>)}</ul>
            </section>
          )}
          <section className="rounded-lg border border-[var(--brand-accent)] bg-[var(--brand-tint)]/60 p-4">
            <h3 className="mb-2 flex items-center gap-1 text-sm font-semibold text-[var(--brand-navy)]"><Lightbulb className="size-4" />Suggested next steps</h3>
            <ol className="space-y-2 text-sm">{m.recommendations.map((r) => <li key={r.label}><p className="font-medium">{r.label}</p><p className="text-xs text-muted-foreground">{r.detail}</p></li>)}</ol>
          </section>
        </aside>
      </div>
    </>
  );
}

function Panel({ title, tag, accent, children }: { title: string; tag: React.ReactNode; accent: "navy" | "blue"; children: React.ReactNode }) {
  return (
    <section className={`rounded-lg border-t-4 bg-white p-4  ${accent === "navy" ? "border-t-[var(--brand-navy)]" : "border-t-[var(--brand-blue)]"}`}>
      <div className="mb-2 flex items-center justify-between gap-2"><h2 className="font-semibold text-[var(--brand-navy)]">{title}</h2>{tag}</div>
      {children}
    </section>
  );
}

function ListPanel({ icon: Icon, title, items, cls }: { icon: React.ComponentType<{ className?: string }>; title: string; items: string[]; cls: string }) {
  return (
    <section className={`rounded-lg border p-4 ${cls}`}>
      <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-[var(--brand-navy)]"><Icon className="size-4" />{title}</h3>
      {items.length ? <ul className="space-y-1 text-sm">{items.map((i) => <li key={i}>• {i}</li>)}</ul> : <p className="text-sm text-muted-foreground">None identified</p>}
    </section>
  );
}
