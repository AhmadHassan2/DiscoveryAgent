"use client";

import { use, useEffect, useState } from "react";
import { Printer } from "lucide-react";
import { ErrorState } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { AnalysisReport } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function PrintPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [r, setR] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.analysis(id).then((e) => (e.report ? setR(e.report) : setError(`Analysis is ${e.status}`))).catch((e) => setError(e.message));
  }, [id]);
  if (error) return <ErrorState message={error} />;
  if (!r) return null;
  return (
    <article className="mx-auto max-w-3xl space-y-5 rounded-lg bg-white p-8 text-sm leading-relaxed  print:shadow-none">
      <div className="no-print flex justify-end"><Button onClick={() => window.print()}><Printer className="size-4" />Print / save as PDF</Button></div>
      <header className="border-b-4 border-[var(--brand-accent)] pb-3">
        <p className="text-xs font-semibold tracking-wider text-primary uppercase">Idea validation report</p>
        <h1 className="text-2xl font-semibold text-[var(--brand-navy)]">{r.idea.title || r.understanding.summary}</h1>
        <p className="text-xs text-muted-foreground">
          {formatDate(r.completed_at)} · Analysis {r.analysis_id} · Data: synthetic mock sources · AI mode: {r.capability_mode} ({r.llm_provider})
        </p>
      </header>
      <section><h2 className="font-semibold text-[var(--brand-navy)]">Idea</h2><p>{r.idea.description}</p></section>
      <section className="rounded-lg bg-[var(--brand-tint)] p-4">
        <h2 className="font-semibold text-[var(--brand-navy)]">{r.verdict.category_label}: {r.verdict.headline}</h2>
        <p>{r.verdict.summary}</p>
        <p className="mt-2"><strong>Recommended action:</strong> {r.verdict.primary_recommendation.label}. {r.verdict.primary_recommendation.detail}</p>
      </section>
      <section>
        <h2 className="font-semibold text-[var(--brand-navy)]">Coverage</h2>
        <p>{r.totals.sources_searched}/{r.totals.sources_requested} sources searched · {r.totals.records_retrieved} records · {r.totals.relevant_initiatives} relevant initiatives</p>
        <p className="text-xs text-muted-foreground">{r.sources.map((s) => `${s.label}: ${s.status === "ok" ? s.records_found : "unavailable"}`).join(" · ")}</p>
      </section>
      {r.matches.map((m) => (
        <section key={m.initiative_id} className="print-break space-y-1 border-t pt-3">
          <h3 className="font-semibold text-[var(--brand-navy)]">{m.name} — {m.category_label} ({Math.round(m.overall_score * 100)}/100)</h3>
          <p className="text-xs">{m.department} · {m.lifecycle.label} ({m.lifecycle.confidence} confidence) · Owner: {m.owner ? `${m.owner.name} (${m.owner.provenance})` : "unknown"}</p>
          <p>{m.explanation}</p>
          {m.recommendations[0] && <p><strong>Next step:</strong> {m.recommendations[0].label}</p>}
          <ul className="list-disc pl-5 text-xs">{m.evidence.map((e) => <li key={e.record_id}>[{e.source_label}] {e.title} ({e.external_key}, {e.source_status ?? "n/a"}, updated {formatDate(e.updated_at)})</li>)}</ul>
        </section>
      ))}
      <section className="border-t pt-3">
        <h2 className="font-semibold text-[var(--brand-navy)]">Limitations</h2>
        <ul className="list-disc pl-5 text-xs">{r.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
        <p className="mt-2 text-xs text-muted-foreground">Scores are a weighted ranking heuristic, not calibrated probabilities.</p>
      </section>
    </article>
  );
}
