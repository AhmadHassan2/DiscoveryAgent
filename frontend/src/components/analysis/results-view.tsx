"use client";

import Link from "next/link";
import { Download, Library, Printer, TriangleAlert, Unlink } from "lucide-react";
import { CategoryBadge, FactLabel, SourceBadge } from "@/components/app/badges";
import { EvidenceList } from "@/components/analysis/evidence";
import { MatchCard } from "@/components/analysis/match-card";
import { RegisterDialog } from "@/components/analysis/register-dialog";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { AnalysisReport, ProgressEvent } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ResultsView({ report, events = [] }: { report: AnalysisReport; events?: ProgressEvent[] }) {
  const v = report.verdict;
  const t = report.totals;
  const failed = report.sources.filter((s) => s.status !== "ok");
  const modeLabel = report.capability_mode === "full" ? `AI: ${report.llm_provider}` : report.capability_mode === "degraded" ? "AI failed: rule-based fallback" : "Demo AI mode (rule-based)";

  return (
    <div className="space-y-6">
      {/* Verdict */}
      <section className="overflow-hidden rounded-2xl bg-[var(--brand-navy)] text-white shadow-sm">
        <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_360px] lg:items-start">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <CategoryBadge category={v.category} size="lg" className="bg-white text-[var(--brand-navy)] ring-0" />
              <span className="text-sm text-blue-200">{modeLabel}</span>
            </div>
            <h2 className="mt-4 text-2xl leading-snug font-semibold sm:text-3xl">{v.headline}</h2>
            <p className="mt-3 max-w-2xl text-base leading-relaxed text-blue-100">{v.summary}</p>
          </div>
          <div className="rounded-xl bg-white p-5 text-[var(--brand-navy)]">
            <p className="text-sm font-medium text-muted-foreground">Recommended next step</p>
            <p className="mt-1 text-lg leading-snug font-semibold">{v.primary_recommendation.label}</p>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{v.primary_recommendation.detail}</p>
          </div>
        </div>
        <div className="no-print flex flex-wrap gap-2 border-t border-white/10 bg-white/5 px-6 py-4 sm:px-8">
          <RegisterDialog report={report} trigger={
            <Button className="h-11 bg-white text-[var(--brand-navy)] hover:bg-blue-50"><Library className="size-4" aria-hidden />Register this idea</Button>
          } />
          <Button asChild variant="ghost" className="h-11 text-white hover:bg-white/10 hover:text-white">
            <a href={api.exportUrl(report.analysis_id)}><Download className="size-4" aria-hidden />Export (.md)</a>
          </Button>
          <Button asChild variant="ghost" className="h-11 text-white hover:bg-white/10 hover:text-white">
            <Link href={`/analysis/${report.analysis_id}/print`}><Printer className="size-4" aria-hidden />Print view</Link>
          </Button>
        </div>
      </section>

      {/* Coverage summary */}
      <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border bg-border sm:grid-cols-4">
        <Stat label="Sources searched" value={`${t.sources_searched} of ${t.sources_requested}`} warn={t.sources_failed > 0} />
        <Stat label="Records retrieved" value={t.records_retrieved} />
        <Stat label="Candidate initiatives" value={t.initiatives_identified} />
        <Stat label="Relevant initiatives" value={t.relevant_initiatives} strong />
      </dl>

      {failed.length > 0 && (
        <div role="alert" className="flex gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          <TriangleAlert className="mt-0.5 size-5 shrink-0" aria-hidden />
          <p><span className="font-semibold">Search not comprehensive.</span> {failed.map((f) => `${f.label}: ${f.error}`).join(" · ")}</p>
        </div>
      )}
      {report.warnings.map((w) => (
        <div key={w} className="rounded-xl border bg-white px-4 py-3 text-sm text-muted-foreground">{w}</div>
      ))}

      <Tabs defaultValue="matches">
        <TabsList className="h-12 w-full justify-start gap-1 rounded-xl border bg-white p-1 sm:w-auto">
          <TabsTrigger value="matches" className="h-10 px-4 data-[state=active]:bg-[var(--brand-navy)] data-[state=active]:text-white">Matches ({report.matches.length})</TabsTrigger>
          <TabsTrigger value="search" className="h-10 px-4 data-[state=active]:bg-[var(--brand-navy)] data-[state=active]:text-white">How we searched</TabsTrigger>
          <TabsTrigger value="limits" className="h-10 px-4 data-[state=active]:bg-[var(--brand-navy)] data-[state=active]:text-white">Limitations</TabsTrigger>
        </TabsList>

        <TabsContent value="matches" className="mt-5 space-y-4">
          {report.matches.length === 0 ? (
            <div className="rounded-xl border border-dashed bg-white p-10 text-center">
              <p className="text-lg font-semibold text-[var(--brand-navy)]">No related initiatives found</p>
              <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
                Nothing in the sources searched overlaps meaningfully with this idea. That doesn&apos;t prove nothing similar exists. Register the idea so others can find it.
              </p>
            </div>
          ) : (
            <>
              <p className="text-sm text-muted-foreground">Ranked by overlap. Select a match to see its evidence, owner and next steps.</p>
              {report.matches.map((m, i) => <MatchCard key={m.initiative_id} match={m} analysisId={report.analysis_id} rank={i + 1} defaultOpen={i === 0} />)}
            </>
          )}
          {report.unlinked_evidence.length > 0 && (
            <section className="rounded-xl border bg-white p-5">
              <h3 className="flex items-center gap-2 font-semibold text-[var(--brand-navy)]"><Unlink className="size-4" aria-hidden />Unlinked evidence</h3>
              <p className="mt-1 mb-3 text-sm text-muted-foreground">Relevant records that can&apos;t be tied to a known initiative. They may point to undocumented work.</p>
              <EvidenceList items={report.unlinked_evidence} />
            </section>
          )}
        </TabsContent>

        <TabsContent value="search" className="mt-5 grid gap-4 lg:grid-cols-2">
          <section className="rounded-xl border bg-white p-5">
            <div className="mb-4 flex items-center justify-between gap-2">
              <h3 className="font-semibold text-[var(--brand-navy)]">How the idea was understood</h3>
              <FactLabel kind={report.understanding.generated_by.startsWith("llm") ? "ai" : "rule"} />
            </div>
            <dl className="space-y-4 text-sm">
              <div><dt className="font-medium text-muted-foreground">Objective</dt><dd className="mt-1">{report.understanding.objective}</dd></div>
              <div><dt className="font-medium text-muted-foreground">Capabilities</dt><dd className="mt-1.5 flex flex-wrap gap-1.5">{report.understanding.capabilities.map((c) => <Chip key={c}>{c}</Chip>)}</dd></div>
              {report.understanding.target_users.length > 0 && <div><dt className="font-medium text-muted-foreground">Target users</dt><dd className="mt-1">{report.understanding.target_users.join(", ")}</dd></div>}
              <div><dt className="font-medium text-muted-foreground">Alternative terms searched</dt><dd className="mt-1.5 flex flex-wrap gap-1.5">{report.understanding.alternative_terms.map((c) => <Chip key={c}>{c}</Chip>)}</dd></div>
              <div><dt className="font-medium text-muted-foreground">Queries</dt><dd className="mt-1"><ul className="list-disc space-y-0.5 pl-5 text-muted-foreground">{report.understanding.search_queries.map((q) => <li key={q}>{q}</li>)}</ul></dd></div>
            </dl>
          </section>
          <div className="space-y-4">
            <section className="rounded-xl border bg-white p-5">
              <h3 className="mb-3 font-semibold text-[var(--brand-navy)]">Source coverage</h3>
              <ul className="divide-y">
                {report.sources.map((s) => (
                  <li key={s.source} className="flex items-center justify-between gap-2 py-2.5 text-sm">
                    <SourceBadge source={s.source} />
                    <span className={cn(s.status === "ok" ? "text-muted-foreground" : "font-medium text-red-700")}>
                      {s.status === "ok" ? `${s.records_found} records · ${s.duration_ms} ms` : "Unavailable"}
                      {s.filtered_by_permissions > 0 && ` · ${s.filtered_by_permissions} hidden by access rules`}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
            {events.length > 0 && (
              <section className="rounded-xl border bg-white p-5">
                <h3 className="mb-3 font-semibold text-[var(--brand-navy)]">Search trace</h3>
                <ol className="space-y-2 text-sm">
                  {events.filter((e) => e.status !== "started" && e.stage !== "done").map((e) => (
                    <li key={e.seq} className="border-l-2 border-[var(--brand-blue)]/30 pl-3">
                      <span className={cn("font-medium", e.status === "failed" && "text-red-700")}>{e.label}</span>
                      {e.detail && <span className="block text-muted-foreground">{e.detail}</span>}
                    </li>
                  ))}
                </ol>
              </section>
            )}
          </div>
        </TabsContent>

        <TabsContent value="limits" className="mt-5">
          <section className="rounded-xl border bg-white p-5">
            <h3 className="mb-3 font-semibold text-[var(--brand-navy)]">What this result can and can&apos;t tell you</h3>
            <ul className="space-y-2.5 text-sm leading-relaxed">{report.limitations.map((l) => <li key={l} className="flex gap-2"><span className="mt-2 size-1.5 shrink-0 rounded-full bg-[var(--brand-blue)]" />{l}</li>)}</ul>
          </section>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Stat({ label, value, warn, strong }: { label: string; value: React.ReactNode; warn?: boolean; strong?: boolean }) {
  return (
    <div className={cn("bg-white px-5 py-4", warn && "bg-amber-50")}>
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className={cn("mt-1 text-2xl font-semibold tabular-nums", strong ? "text-[var(--brand-blue)]" : "text-[var(--brand-navy)]")}>{value}</dd>
    </div>
  );
}

function Chip({ children }: { children: React.ReactNode }) {
  return <span className="rounded-md bg-secondary px-2 py-1 text-xs text-secondary-foreground">{children}</span>;
}
