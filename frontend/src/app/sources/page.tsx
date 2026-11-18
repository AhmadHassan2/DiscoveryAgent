"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CircleCheck, CircleX, Lock, Search, ShieldCheck } from "lucide-react";
import { ErrorState, PageHeader } from "@/components/app/app-shell";
import { LifecycleBadge, SOURCE_META, SourceBadge } from "@/components/app/badges";
import { RelationshipGraph } from "@/components/app/relationship-graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { GraphResponse, InitiativeSummary, SourceRecordRow, SourceSystem, SourcesOverview } from "@/lib/types";
import { cn, relativeDays } from "@/lib/utils";

export default function SourcesPage() {
  const [overview, setOverview] = useState<SourcesOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.sources().then(setOverview).catch((e) => setError(e.message)); }, []);
  return (
    <>
      <PageHeader title="Source Explorer" description="Look at the simulated systems, the records they index, and how records are linked to initiatives. Use this to show how the agent reached its conclusions." />
      {error && <ErrorState message={error} />}
      <Tabs defaultValue="systems">
        <TabsList className="mb-4 bg-white">
          <TabsTrigger value="systems">Connected systems</TabsTrigger>
          <TabsTrigger value="records">Indexed records</TabsTrigger>
          <TabsTrigger value="initiatives">Initiatives</TabsTrigger>
          <TabsTrigger value="graph">Relationship graph</TabsTrigger>
        </TabsList>
        <TabsContent value="systems">{overview ? <Systems overview={overview} /> : <Skeleton className="h-64" />}</TabsContent>
        <TabsContent value="records"><Records /></TabsContent>
        <TabsContent value="initiatives"><Initiatives /></TabsContent>
        <TabsContent value="graph"><Graph /></TabsContent>
      </Tabs>
    </>
  );
}

function Systems({ overview }: { overview: SourcesOverview }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 rounded-lg border border-[var(--brand-accent)] bg-[var(--brand-tint)]/60 p-4 text-sm text-[#0b1f4d]">
        <ShieldCheck className="size-5 shrink-0" />
        <p><strong>Mock integrations.</strong> Every connector is read-only and searches synthetic records stored locally. The search, correlation and analysis are real. Only the source systems are simulated. Real connectors plug into the same interface.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {overview.sources.map((s) => {
          const Icon = SOURCE_META[s.source].icon;
          return (
            <article key={s.source} className="rounded-lg border bg-white p-4">
              <div className="flex items-center justify-between">
                <h3 className="flex items-center gap-2 font-semibold text-[var(--brand-navy)]"><span className="grid size-8 place-items-center rounded-lg bg-secondary"><Icon className="size-4 text-primary" /></span>{s.display_name}</h3>
                {s.status === "ok"
                  ? <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700"><CircleCheck className="size-4" />Healthy</span>
                  : <span className="inline-flex items-center gap-1 text-xs font-medium text-red-700"><CircleX className="size-4" />{s.error ?? s.status}</span>}
              </div>
              <p className="mt-2 text-xs text-muted-foreground">{s.description}</p>
              <dl className="mt-3 grid grid-cols-3 gap-2 text-xs">
                <div><dt className="text-muted-foreground">Records</dt><dd className="text-lg font-semibold text-[var(--brand-navy)]">{s.record_count}</dd></div>
                <div><dt className="text-muted-foreground">Mode</dt><dd className="font-medium">{s.mode}</dd></div>
                <div><dt className="text-muted-foreground">Access</dt><dd className="font-medium">{s.read_only ? "read-only" : "read/write"}</dd></div>
              </dl>
              <div className="mt-2 flex flex-wrap gap-1">{Object.entries(s.record_types).map(([t, c]) => <span key={t} className="rounded bg-muted px-1.5 py-0.5 text-xs">{t.replaceAll("_", " ")} · {c}</span>)}</div>
              {s.last_indexed_at && <p className="mt-2 text-xs text-muted-foreground">Latest record activity {relativeDays(s.last_indexed_at)}</p>}
            </article>
          );
        })}
      </div>
    </div>
  );
}

function Records() {
  const [source, setSource] = useState<SourceSystem>("confluence");
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<SourceRecordRow[] | null>(null);
  useEffect(() => { setRows(null); api.sourceRecords(source).then(setRows).catch(() => setRows([])); }, [source]);
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {(Object.keys(SOURCE_META) as SourceSystem[]).map((s) => (
          <button key={s} onClick={() => setSource(s)} className={cn("rounded-full", s === source && "ring-2 ring-[var(--brand-accent)]")}><SourceBadge source={s} /></button>
        ))}
      </div>
      <form className="flex max-w-md gap-2" onSubmit={(e) => { e.preventDefault(); setRows(null); api.sourceRecords(source, q).then(setRows); }}>
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Filter ${SOURCE_META[source].label} records`} className="bg-white" />
        <Button type="submit" variant="outline"><Search className="size-4" /></Button>
      </form>
      {rows === null ? <Skeleton className="h-64" /> : (
        <div className="overflow-x-auto rounded-lg border bg-white">
          <Table>
            <TableHeader><TableRow><TableHead>Record</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead><TableHead>Owner</TableHead><TableHead>Linked initiative</TableHead><TableHead>Updated</TableHead></TableRow></TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.id} className="align-top">
                  <TableCell className="max-w-sm whitespace-normal">
                    <p className="flex items-center gap-1 font-medium text-[var(--brand-navy)]">{r.restricted && <Lock className="size-3.5 text-amber-700" aria-label="restricted" />}{r.title}</p>
                    <p className="font-mono text-xs text-muted-foreground">{r.external_key}</p>
                    {r.restricted && <p className="text-xs text-amber-800">Content hidden: restricted access ({String(r.acl.groups)})</p>}
                  </TableCell>
                  <TableCell className="text-xs">{r.record_type.replaceAll("_", " ")}</TableCell>
                  <TableCell className="text-xs">{r.source_status ?? "—"}</TableCell>
                  <TableCell className="text-xs">{r.owner ?? r.author ?? "—"}</TableCell>
                  <TableCell className="text-xs whitespace-normal">
                    {r.initiative_id ? <><Link href={`/projects/${r.initiative_id}`} className="font-medium text-primary hover:underline">{r.initiative_id}</Link><p className="text-xs text-muted-foreground">{r.link_reason}</p></> : <span className="text-muted-foreground">Unlinked</span>}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{relativeDays(r.updated_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function Initiatives() {
  const [rows, setRows] = useState<InitiativeSummary[] | null>(null);
  useEffect(() => { api.projects().then(setRows).catch(() => setRows([])); }, []);
  if (!rows) return <Skeleton className="h-64" />;
  return (
    <div className="overflow-x-auto rounded-lg border bg-white">
      <Table>
        <TableHeader><TableRow><TableHead>Initiative</TableHead><TableHead>Department</TableHead><TableHead>Owner</TableHead><TableHead>Status</TableHead><TableHead>Evidence</TableHead><TableHead>Last activity</TableHead></TableRow></TableHeader>
        <TableBody>
          {rows.map((p) => (
            <TableRow key={p.id}>
              <TableCell><Link href={`/projects/${p.id}`} className="font-medium text-[var(--brand-navy)] hover:text-primary">{p.name}</Link><p className="font-mono text-xs text-muted-foreground">{p.id}</p></TableCell>
              <TableCell className="text-xs">{p.department}<p className="text-muted-foreground">{p.team}</p></TableCell>
              <TableCell className="text-xs">{p.owner_name ?? "—"}</TableCell>
              <TableCell><LifecycleBadge stage={p.status} /></TableCell>
              <TableCell><span className="flex flex-wrap gap-1">{p.sources.map((s) => <SourceBadge key={s} source={s} />)}</span><span className="text-xs text-muted-foreground">{p.record_count} records</span></TableCell>
              <TableCell className="text-xs text-muted-foreground">{relativeDays(p.last_activity_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function Graph() {
  const [withRecords, setWithRecords] = useState(true);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  useEffect(() => { setGraph(null); api.graph(withRecords).then(setGraph); }, [withRecords]);
  return (
    <div className="space-y-3">
      <label className="flex items-center gap-2 text-sm"><Switch checked={withRecords} onCheckedChange={setWithRecords} />Show source records</label>
      {graph ? <RelationshipGraph graph={graph} /> : <Skeleton className="h-[500px]" />}
    </div>
  );
}
