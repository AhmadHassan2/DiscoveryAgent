"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, ChevronRight, FlaskConical, Library, Network } from "lucide-react";
import { ErrorState } from "@/components/app/app-shell";
import { CategoryBadge } from "@/components/app/badges";
import { IdeaForm } from "@/components/app/idea-form";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { AnalysisSummary, DemoScenario, StatsResponse } from "@/lib/types";
import { relativeDays } from "@/lib/utils";

export default function Home() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [recent, setRecent] = useState<AnalysisSummary[] | null>(null);
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    Promise.all([api.stats(), api.analyses(5), api.scenarios()])
      .then(([s, a, d]) => { setStats(s); setRecent(a); setScenarios(d.slice(0, 3)); })
      .catch((e) => setError(e.message));
  };
  useEffect(load, []);

  return (
    <div className="space-y-10">
      {/* Primary task */}
      <section className="overflow-hidden rounded-2xl border bg-white shadow-sm">
        <div className="bg-[var(--brand-navy)] px-6 py-8 text-white sm:px-10">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">Has someone already built this?</h1>
          <p className="mt-3 max-w-2xl text-base leading-relaxed text-blue-100">
            Describe your idea. We&apos;ll search Confluence, Jira, GitHub, SharePoint, Teams, ServiceNow and the Idea Registry, and tell you
            who to talk to before you start building.
          </p>
        </div>
        <div className="px-6 py-6 sm:px-10">
          <IdeaForm compact />
          {scenarios.length > 0 && (
            <div className="mt-5 border-t pt-5">
              <p className="mb-2 text-sm font-medium text-muted-foreground">Or try an example</p>
              <div className="flex flex-wrap gap-2">
                {scenarios.map((s) => (
                  <Link key={s.id} href={`/submit?q=${encodeURIComponent(s.idea.description)}`}
                    className="inline-flex min-h-10 items-center rounded-full border bg-background px-4 text-sm text-[var(--brand-navy)] hover:border-[var(--brand-blue)] hover:bg-secondary">
                    {s.idea.title ?? s.title}
                  </Link>
                ))}
                <Link href="/demo" className="inline-flex min-h-10 items-center gap-1 rounded-full px-3 text-sm font-medium text-[var(--brand-blue)] hover:underline">
                  All demo scenarios <ArrowRight className="size-4" />
                </Link>
              </div>
            </div>
          )}
        </div>
      </section>

      {error && <ErrorState message={error} onRetry={load} />}

      {/* Where to go next */}
      <section className="grid gap-4 md:grid-cols-3">
        <ActionTile href="/demo" icon={FlaskConical} title="Run a demo scenario" text="Duplicate, partial overlap, abandoned and deployed examples." />
        <ActionTile href="/registry" icon={Library} title="Browse the Idea Registry" text={stats ? `${stats.registered_ideas} registered ideas from employees.` : "Ideas registered by employees."} />
        <ActionTile href="/sources" icon={Network} title="Explore connected sources" text={stats ? `${stats.records} records across ${stats.initiatives} initiatives.` : "Systems, records and relationships."} />
      </section>

      {/* Recent activity */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[var(--brand-navy)]">Recent searches</h2>
          <Link href="/history" className="text-sm font-medium text-[var(--brand-blue)] hover:underline">View all</Link>
        </div>
        {recent === null ? <Skeleton className="h-40 rounded-xl" /> : recent.length === 0 ? (
          <p className="rounded-xl border border-dashed bg-white p-8 text-center text-muted-foreground">No searches yet. Check an idea above to get started.</p>
        ) : (
          <ul className="divide-y overflow-hidden rounded-xl border bg-white">
            {recent.map((a) => (
              <li key={a.id}>
                <Link href={`/analysis/${a.id}`} className="flex items-center gap-4 px-5 py-4 hover:bg-secondary/60">
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-[var(--brand-navy)]">{a.title || a.idea_text}</p>
                    <p className="text-sm text-muted-foreground">{a.top_initiative_name ? `Top match: ${a.top_initiative_name}` : "No significant match"} · {relativeDays(a.created_at)}</p>
                  </div>
                  {a.top_category && <CategoryBadge category={a.top_category} />}
                  <ChevronRight className="size-5 text-slate-400" aria-hidden />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      {stats && (
        <p className="text-sm text-muted-foreground">
          Index: {stats.initiatives} initiatives · {stats.records} source records · {stats.departments} departments · {stats.sources} connected sources (mock) · {stats.analyses_run} checks run
        </p>
      )}
    </div>
  );
}

function ActionTile({ href, icon: Icon, title, text }: { href: string; icon: React.ComponentType<{ className?: string }>; title: string; text: string }) {
  return (
    <Link href={href} className="group flex items-start gap-4 rounded-xl border bg-white p-5 transition-shadow hover:border-[var(--brand-blue)] hover:shadow-md">
      <span className="grid size-11 shrink-0 place-items-center rounded-lg bg-secondary text-[var(--brand-navy)]"><Icon className="size-5" /></span>
      <span className="min-w-0">
        <span className="flex items-center gap-1 font-semibold text-[var(--brand-navy)]">{title}<ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" /></span>
        <span className="mt-1 block text-sm text-muted-foreground">{text}</span>
      </span>
    </Link>
  );
}
