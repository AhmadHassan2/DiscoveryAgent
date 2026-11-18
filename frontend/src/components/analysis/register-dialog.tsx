"use client";

import Link from "next/link";
import { useState } from "react";
import { CircleCheck, LoaderCircle, TriangleAlert } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api, ApiError, isRegistrationBlocked } from "@/lib/api";
import type { AnalysisReport, RegisteredIdea } from "@/lib/types";

export function RegisterDialog({ report, trigger }: { report: AnalysisReport; trigger: React.ReactNode }) {
  const strong = report.matches.filter((m) => m.category === "near_duplicate" || m.category === "strong_overlap");
  const [open, setOpen] = useState(false);
  const [ack, setAck] = useState(false);
  const [note, setNote] = useState("");
  const [submitter, setSubmitter] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<RegisteredIdea | null>(null);
  const [error, setError] = useState<string | null>(null);
  const needsAck = strong.length > 0;

  async function register() {
    setBusy(true);
    setError(null);
    try {
      const idea = await api.registerIdea({
        idea: report.idea,
        analysis_id: report.analysis_id,
        submitted_by: submitter.trim() || undefined,
        acknowledge_overlap: ack,
        acknowledgement_note: note.trim() || undefined,
      });
      setResult(idea);
      toast.success(`Registered as ${idea.id}`);
    } catch (e) {
      if (isRegistrationBlocked(e)) setError(e.body.detail);
      else setError(e instanceof ApiError ? e.message : "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) { setResult(null); setError(null); } }}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        {result ? (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-[var(--brand-navy)]"><CircleCheck className="size-5 text-primary" />Idea registered: {result.id}</DialogTitle>
              <DialogDescription>Other employees can now find it when they search. Next, take it through your normal approval process.</DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button asChild><Link href={`/registry?highlight=${result.id}`}>Open in Idea Registry</Link></Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="text-[var(--brand-navy)]">Register this idea</DialogTitle>
              <DialogDescription>
                Registering makes your idea discoverable, so others don&apos;t duplicate it. It uses this overlap check ({report.analysis_id}).
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              {needsAck && (
                <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm">
                  <p className="flex items-center gap-1.5 font-semibold text-blue-900"><TriangleAlert className="size-4" />Strong overlap detected</p>
                  <ul className="mt-1 list-disc pl-5 text-blue-900">
                    {strong.map((m) => <li key={m.initiative_id}>{m.name}{m.owner ? ` (owner: ${m.owner.name})` : ""}</li>)}
                  </ul>
                  <label className="mt-3 flex items-start gap-2">
                    <Checkbox checked={ack} onCheckedChange={(v) => setAck(!!v)} className="mt-0.5 bg-white" />
                    <span>I have reviewed these initiatives and contacted their owners. I still want to register a separate idea.</span>
                  </label>
                  <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Why is a separate initiative needed? (optional)" className="mt-2 bg-white" rows={2} />
                </div>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="submitter">Your name or email (optional)</Label>
                <Input id="submitter" value={submitter} onChange={(e) => setSubmitter(e.target.value)} placeholder="demo.user@northbridge.example" />
              </div>
              {error && <p role="alert" className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
              <Button onClick={register} disabled={busy || (needsAck && !ack)}>
                {busy && <LoaderCircle className="size-4 animate-spin" />}Register idea
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
