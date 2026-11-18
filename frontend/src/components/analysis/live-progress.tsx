"use client";

import { CircleCheck, CircleX, LoaderCircle, Circle } from "lucide-react";
import { SOURCE_META } from "@/components/app/badges";
import type { ProgressEvent, SourceSystem } from "@/lib/types";
import { cn } from "@/lib/utils";

type StageState = "pending" | "running" | "done" | "failed";

interface StageRow { key: string; label: string; state: StageState; detail?: string | null; source?: SourceSystem | null; chips?: string[] }

const ORDER = ["understand", "queries", "search", "correlate", "analyze", "ai_review", "report"];

export function buildStages(events: ProgressEvent[], requestedSources: SourceSystem[]): StageRow[] {
  const latest = new Map<string, ProgressEvent>();
  for (const e of events) latest.set(e.stage, e);
  const state = (key: string): StageState => {
    const e = latest.get(key);
    if (!e) return "pending";
    return e.status === "completed" ? "done" : e.status === "failed" ? "failed" : "running";
  };
  const rows: StageRow[] = [];
  for (const key of ORDER) {
    if (key === "search") {
      for (const s of requestedSources) {
        const k = `search:${s}`;
        rows.push({ key: k, label: `Searching ${SOURCE_META[s].label}`, state: state(k), detail: latest.get(k)?.detail, source: s });
      }
      continue;
    }
    if (key === "ai_review" && !latest.has("ai_review")) continue;
    const e = latest.get(key);
    const label = { understand: "Understanding idea", queries: "Generating search terms", correlate: "Correlating records", analyze: "Analyzing project overlap", ai_review: "AI review of top matches", report: "Preparing results" }[key] ?? key;
    const chips = key === "queries" ? ((e?.data?.alternative_terms as string[]) ?? []).slice(0, 6) : key === "understand" ? ((e?.data?.concepts as string[]) ?? []).slice(0, 6) : undefined;
    rows.push({ key, label, state: state(key), detail: e?.detail, chips });
  }
  return rows;
}

export function LiveProgress({ events, sources }: { events: ProgressEvent[]; sources: SourceSystem[] }) {
  const rows = buildStages(events, sources);
  const done = rows.filter((r) => r.state === "done" || r.state === "failed").length;
  return (
    <div className="rounded-lg border bg-white p-6 " aria-live="polite">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-[var(--brand-navy)]">Searching internal systems</h2>
          <p className="text-sm text-muted-foreground">Each step below is reported live by the backend as it runs.</p>
        </div>
        <span className="text-sm font-medium text-primary">{done}/{rows.length} steps</span>
      </div>
      <div className="mb-5 h-2 overflow-hidden rounded-full bg-secondary">
        <div className="h-full rounded-full bg-[var(--brand-navy)] transition-all duration-500" style={{ width: `${(done / Math.max(rows.length, 1)) * 100}%` }} />
      </div>
      <ol className="space-y-1">
        {rows.map((r) => (
          <li key={r.key} className={cn("flex items-start gap-3 rounded-md px-2 py-2", r.state === "running" && "bg-secondary")}>
            <StageIcon state={r.state} />
            <div className="min-w-0 flex-1">
              <p className={cn("text-sm font-medium", r.state === "pending" ? "text-muted-foreground" : "text-foreground")}>{r.label}</p>
              {r.detail && <p className={cn("text-xs", r.state === "failed" ? "text-red-700" : "text-muted-foreground")}>{r.detail}</p>}
              {r.chips && r.chips.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {r.chips.map((c) => (
                    <span key={c} className="rounded bg-[var(--brand-tint)] px-1.5 py-0.5 text-xs text-blue-900">{c}</span>
                  ))}
                </div>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function StageIcon({ state }: { state: StageState }) {
  if (state === "done") return <CircleCheck className="mt-0.5 size-5 text-primary" aria-label="done" />;
  if (state === "failed") return <CircleX className="mt-0.5 size-5 text-red-600" aria-label="failed" />;
  if (state === "running") return <LoaderCircle className="mt-0.5 size-5 animate-spin text-[var(--brand-blue)]" aria-label="running" />;
  return <Circle className="mt-0.5 size-5 text-slate-300" aria-label="pending" />;
}
