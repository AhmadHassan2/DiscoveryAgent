"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { Boxes, Building2, ExternalLink, Mail, User } from "lucide-react";
import { Breadcrumbs, ErrorState, PageHeader } from "@/components/app/app-shell";
import { FactLabel, LifecycleBadge, SourceBadge } from "@/components/app/badges";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { InitiativeDetail } from "@/lib/types";
import { formatDate, relativeDays } from "@/lib/utils";

export default function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [p, setP] = useState<InitiativeDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.project(id).then(setP).catch((e) => setError(e.message)); }, [id]);
  if (error) return <ErrorState message={error} />;
  if (!p) return <Skeleton className="h-96" />;
  return (
    <>
      <Breadcrumbs items={[{ label: "Source Explorer", href: "/sources" }, { label: p.name }]} />
      <PageHeader eyebrow={`Initiative Index · ${p.id}`} title={p.name} description={p.description} actions={<LifecycleBadge stage={p.status} />} />
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          <section className="rounded-lg border bg-white p-5">
            <h2 className="mb-1 text-sm font-semibold text-[var(--brand-navy)]">Business objective</h2>
            <p className="text-sm">{p.business_objective}</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-3 text-sm">
              <List title="Core features" items={p.core_features} />
              <List title="Target users" items={p.target_users} />
              <List title="Technologies" items={p.technologies} />
            </div>
            {p.notes && <p className="mt-4 rounded bg-muted p-2 text-xs">{p.notes}</p>}
          </section>
          <section>
            <div className="mb-2 flex items-center gap-2"><h2 className="text-sm font-semibold text-[var(--brand-navy)]">Linked source records ({p.records.length})</h2><FactLabel kind="fact" /></div>
            <ul className="divide-y rounded-lg border bg-white">
              {p.records.map((r) => (
                <li key={r.id} className="flex items-start gap-3 p-3">
                  <SourceBadge source={r.source} className="mt-0.5 w-36 shrink-0 justify-start" />
                  <div className="min-w-0 flex-1">
                    <a href={r.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm font-medium text-[var(--brand-navy)] hover:text-primary">{r.title}<ExternalLink className="size-3" /></a>
                    <p className="text-xs text-muted-foreground"><span className="font-mono">{r.external_key}</span> · {r.record_type.replaceAll("_", " ")} · {r.source_status ?? "—"} · updated {relativeDays(r.updated_at)}</p>
                    <p className="mt-1 line-clamp-2 text-xs">{r.content}</p>
                    <p className="mt-1 text-xs text-primary">Correlation: {r.link_reason}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>
        <aside className="space-y-4">
          <section className="rounded-lg border bg-white p-4 text-sm">
            <h2 className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Ownership</h2>
            <p className="flex items-center gap-1.5 font-medium"><User className="size-4 text-primary" />{p.owner_name ?? "Unknown"}</p>
            {p.owner_email && <a href={`mailto:${p.owner_email}`} className="flex items-center gap-1 text-xs text-primary hover:underline"><Mail className="size-3" />{p.owner_email}</a>}
            <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground"><Building2 className="size-3.5" />{p.department} · {p.team}</p>
            <p className="mt-2 text-xs text-muted-foreground">Created {formatDate(p.created_at)} · last activity {relativeDays(p.last_activity_at)}</p>
          </section>
          {p.reusable_components.length > 0 && (
            <section className="rounded-lg border bg-white p-4">
              <h2 className="mb-2 flex items-center gap-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase"><Boxes className="size-3.5" />Reusable components</h2>
              <ul className="list-disc space-y-0.5 pl-4 text-sm">{p.reusable_components.map((c) => <li key={c}>{c}</li>)}</ul>
            </section>
          )}
          <section className="rounded-lg border bg-white p-4">
            <h2 className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Related initiatives</h2>
            {p.related.length === 0 ? <p className="text-sm text-muted-foreground">None found.</p> : (
              <ul className="space-y-2 text-sm">
                {p.related.map((r) => (
                  <li key={r.id}>
                    {r.id.startsWith("INIT") ? <Link href={`/projects/${r.id}`} className="font-medium text-primary hover:underline">{r.name}</Link> : <Link href={`/registry?highlight=${r.id}`} className="font-medium text-primary hover:underline">{r.name}</Link>}
                    <p className="text-xs text-muted-foreground">{r.reason}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
          {p.aliases.length > 0 && <p className="text-xs text-muted-foreground">Also known as: {p.aliases.join(", ")}</p>}
        </aside>
      </div>
    </>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">{title}</h3>
      <ul className="space-y-0.5 text-xs">{items.map((i) => <li key={i}>• {i}</li>)}</ul>
    </div>
  );
}
