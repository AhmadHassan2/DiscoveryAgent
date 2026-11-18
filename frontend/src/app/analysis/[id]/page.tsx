"use client";

import { use, useEffect, useRef, useState } from "react";
import { LoaderCircle } from "lucide-react";
import { Breadcrumbs, ErrorState, PageHeader } from "@/components/app/app-shell";
import { SOURCE_META } from "@/components/app/badges";
import { LiveProgress } from "@/components/analysis/live-progress";
import { ResultsView } from "@/components/analysis/results-view";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnalysis } from "@/lib/use-analysis";
import type { SourceSystem } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function AnalysisPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { envelope, events, error, reload } = useAnalysis(id);
  // If we watched the run live, keep the progress view on screen briefly after completion.
  const sawRunning = useRef(false);
  const [hold, setHold] = useState(false);
  const status = envelope?.status;
  useEffect(() => {
    if (status === "running") sawRunning.current = true;
    if (status === "completed" && sawRunning.current) {
      setHold(true);
      const t = setTimeout(() => setHold(false), 1400);
      return () => clearTimeout(t);
    }
  }, [status]);

  if (error) return <ErrorState message={error} onRetry={() => void reload()} />;
  if (!envelope) return <div className="space-y-4"><Skeleton className="h-10 w-2/3" /><Skeleton className="h-64 w-full" /></div>;

  const idea = envelope.request.idea;
  const sources = (envelope.request.sources ?? (Object.keys(SOURCE_META) as SourceSystem[])) as SourceSystem[];

  return (
    <>
      <Breadcrumbs items={[{ label: "Search history", href: "/history" }, { label: idea.title || "Idea validation" }]} />
      <PageHeader
        eyebrow={envelope.status === "running" ? "Analysis in progress" : `Idea validation report · ${formatDate(envelope.created_at)}`}
        title={idea.title || "Idea validation"}
        description={<span className="line-clamp-3">&ldquo;{idea.description}&rdquo;</span>}
      />
      {(envelope.status === "running" || hold) && (
        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
          <LiveProgress events={events} sources={sources} />
          <div className="flex items-start gap-2 rounded-lg border bg-white p-4 text-sm text-muted-foreground">
            <LoaderCircle className="mt-0.5 size-4 animate-spin text-primary" />
            {hold ? "Analysis complete. Opening results…" : "Results will appear here automatically when the analysis finishes."}
          </div>
        </div>
      )}
      {envelope.status === "failed" && <ErrorState message={envelope.error ?? "The analysis failed."} />}
      {envelope.status === "completed" && envelope.report && !hold && <ResultsView report={envelope.report} events={events} />}
    </>
  );
}
