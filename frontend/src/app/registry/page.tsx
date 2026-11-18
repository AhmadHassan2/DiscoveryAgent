"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import { LoaderCircle, Plus, Search, TriangleAlert } from "lucide-react";
import { toast } from "sonner";
import { ErrorState, PageHeader } from "@/components/app/app-shell";
import { CategoryBadge } from "@/components/app/badges";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { api, ApiError, isRegistrationBlocked } from "@/lib/api";
import type { RegisteredIdea, RegistrationBlocked } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

const STATUS_STYLE: Record<string, string> = {
  registered: "bg-blue-50 text-blue-900 ring-blue-200",
  registered_with_overlap: "bg-blue-50 text-blue-900 ring-blue-200",
  under_review: "bg-indigo-50 text-indigo-900 ring-indigo-200",
};

function RegistryInner() {
  const highlight = useSearchParams().get("highlight");
  const [q, setQ] = useState("");
  const [ideas, setIdeas] = useState<RegisteredIdea[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback((query?: string) => {
    api.ideas(query).then(setIdeas).catch((e) => setError(e.message));
  }, []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (highlight && ideas) document.getElementById(highlight)?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlight, ideas]);

  return (
    <>
      <PageHeader title="Idea Registry" description="Ideas registered by employees. Registering makes an idea discoverable in future searches. Every registration runs an overlap check first, so obvious duplicates can't be registered without acknowledgement."
        actions={<RegisterIdeaDialog onDone={() => load(q)} />} />
      <form className="mb-4 flex max-w-lg gap-2" onSubmit={(e) => { e.preventDefault(); load(q); }} role="search">
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search ideas, owners or departments" className="bg-white" aria-label="Search ideas" />
        <Button type="submit" variant="outline"><Search className="size-4" />Search</Button>
      </form>
      {error && <ErrorState message={error} />}
      {ideas === null ? <Skeleton className="h-64" /> : ideas.length === 0 ? (
        <p className="rounded-lg border border-dashed bg-white p-8 text-center text-sm text-muted-foreground">No ideas match your search.</p>
      ) : (
        <div className="grid gap-3">
          {ideas.map((i) => (
            <article id={i.id} key={i.id} className={cn("rounded-lg border bg-white p-4 transition-shadow", highlight === i.id && "ring-2 ring-[var(--brand-accent)]")}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-xs text-muted-foreground"><span className="font-mono">{i.id}</span> · {formatDate(i.created_at)}</p>
                  <h2 className="font-semibold text-[var(--brand-navy)]">{i.title}</h2>
                </div>
                <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium ring-1", STATUS_STYLE[i.status] ?? "bg-slate-50 ring-slate-200")}>{i.status.replaceAll("_", " ")}</span>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{i.description}</p>
              <dl className="mt-3 grid gap-x-6 gap-y-1 text-xs sm:grid-cols-3">
                <div><dt className="text-muted-foreground">Owner</dt><dd className="font-medium">{i.submitted_by}</dd></div>
                <div><dt className="text-muted-foreground">Department / team</dt><dd>{i.department ?? "—"}{i.team ? ` · ${i.team}` : ""}</dd></div>
                <div><dt className="text-muted-foreground">Overlap check</dt><dd>{i.analysis_id ? <Link className="text-primary hover:underline" href={`/analysis/${i.analysis_id}`}>View report</Link> : "Seeded record"}</dd></div>
              </dl>
              {i.related_initiatives.length > 0 && (
                <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
                  <span className="text-muted-foreground">Related:</span>
                  {i.related_initiatives.map((r) => (
                    r.type === "initiative"
                      ? <Link key={r.id} href={`/projects/${r.id}`} className="rounded bg-secondary px-1.5 py-0.5 text-secondary-foreground hover:underline">{r.name}</Link>
                      : <span key={r.id} className="rounded bg-blue-50 px-1.5 py-0.5 text-blue-900">{r.name}</span>
                  ))}
                </div>
              )}
              {i.acknowledged_overlap && (
                <p className="mt-2 rounded bg-blue-50 px-2 py-1 text-xs text-blue-900">
                  Overlap acknowledged by the submitter{i.acknowledged_overlap.note ? `: “${i.acknowledged_overlap.note}”` : "."}
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </>
  );
}

function RegisterIdeaDialog({ onDone }: { onDone: () => void }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [department, setDepartment] = useState("");
  const [submitter, setSubmitter] = useState("");
  const [blocked, setBlocked] = useState<RegistrationBlocked | null>(null);
  const [ack, setAck] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const idea = await api.registerIdea({
        idea: { title: title || null, description, department: department || null },
        submitted_by: submitter || undefined,
        analysis_id: blocked?.analysis_id,
        acknowledge_overlap: ack,
      });
      toast.success(`Registered ${idea.id}`);
      setOpen(false);
      setBlocked(null); setAck(false); setTitle(""); setDescription(""); setDepartment("");
      onDone();
    } catch (e) {
      if (isRegistrationBlocked(e)) setBlocked(e.body);
      else setError(e instanceof ApiError ? e.message : "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild><Button><Plus className="size-4" />Register an idea</Button></DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-[var(--brand-navy)]">Register an idea</DialogTitle>
          <DialogDescription>An overlap check runs automatically before the idea is registered.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5"><Label htmlFor="r-title">Title</Label><Input id="r-title" value={title} onChange={(e) => setTitle(e.target.value)} /></div>
          <div className="space-y-1.5"><Label htmlFor="r-desc">Description *</Label><Textarea id="r-desc" value={description} onChange={(e) => { setDescription(e.target.value); setBlocked(null); setAck(false); }} rows={4} /></div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5"><Label htmlFor="r-dept">Department</Label><Input id="r-dept" value={department} onChange={(e) => setDepartment(e.target.value)} /></div>
            <div className="space-y-1.5"><Label htmlFor="r-sub">Your name / email</Label><Input id="r-sub" value={submitter} onChange={(e) => setSubmitter(e.target.value)} /></div>
          </div>
          {blocked && (
            <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
              <p className="flex items-center gap-1.5 font-semibold"><TriangleAlert className="size-4" />Possible duplicate</p>
              <p className="mt-1">{blocked.detail}</p>
              <ul className="mt-2 space-y-1">
                {blocked.overlapping.map((o) => <li key={o.id} className="flex items-center gap-2"><CategoryBadge category={o.category} />{o.name}{o.owner ? ` · ${o.owner}` : ""}</li>)}
              </ul>
              <Link href={`/analysis/${blocked.analysis_id}`} className="mt-2 inline-block font-medium text-primary underline">Review the full overlap report</Link>
              <label className="mt-2 flex items-start gap-2"><Checkbox checked={ack} onCheckedChange={(v) => setAck(!!v)} className="mt-0.5 bg-white" />I have contacted the owners and still need a separate idea.</label>
            </div>
          )}
          {error && <p role="alert" className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={submit} disabled={busy || description.trim().length < 10 || (!!blocked && !ack)}>
            {busy && <LoaderCircle className="size-4 animate-spin" />}{busy ? "Checking for overlap…" : blocked ? "Register anyway" : "Check & register"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function RegistryPage() {
  return <Suspense><RegistryInner /></Suspense>;
}
