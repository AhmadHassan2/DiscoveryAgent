"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LoaderCircle, Play } from "lucide-react";
import { ErrorState, PageHeader } from "@/components/app/app-shell";
import { CategoryBadge } from "@/components/app/badges";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { DemoScenario, OverlapCategory } from "@/lib/types";

const EXPECTED: Record<string, OverlapCategory> = {
  "strong-duplicate": "near_duplicate", "partial-overlap": "partial_overlap", "no-match": "no_significant_match",
  abandoned: "near_duplicate", deployed: "near_duplicate", "different-terminology": "near_duplicate", "similar-keywords": "near_duplicate",
};

export default function DemoPage() {
  const router = useRouter();
  const [scenarios, setScenarios] = useState<DemoScenario[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState<string | null>(null);

  useEffect(() => { api.scenarios().then(setScenarios).catch((e) => setError(e.message)); }, []);

  async function launch(s: DemoScenario) {
    setRunning(s.id);
    try {
      const res = await api.startAnalysis({ idea: s.idea, scenario_id: s.id });
      router.push(`/analysis/${res.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start");
      setRunning(null);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Presentation mode" title="Demo scenarios"
        description="Each scenario sends a predefined idea through the real pipeline. Nothing is pre-recorded, and the results are repeatable because the synthetic data and deterministic scoring don't change." />
      {error && <ErrorState message={error} />}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {scenarios === null ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-56" />) : scenarios.map((s) => (
          <article key={s.id} className="flex flex-col rounded-xl border bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="grid size-8 place-items-center rounded-lg bg-[var(--brand-navy)] text-sm font-bold text-white">{s.case}</span>
              {EXPECTED[s.id] && <span className="flex items-center gap-1 text-xs text-muted-foreground">Expected <CategoryBadge category={EXPECTED[s.id]} /></span>}
            </div>
            <h2 className="mt-3 font-semibold text-[var(--brand-navy)]">{s.title}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{s.summary}</p>
            <blockquote className="mt-3 flex-1 border-l-2 border-[var(--brand-blue)]/40 pl-3 text-sm italic">&ldquo;{s.idea.description}&rdquo;</blockquote>
            <Button className="mt-4" onClick={() => launch(s)} disabled={!!running}>
              {running === s.id ? <LoaderCircle className="size-4 animate-spin" /> : <Play className="size-4" />}Run scenario
            </Button>
          </article>
        ))}
      </div>
    </>
  );
}
