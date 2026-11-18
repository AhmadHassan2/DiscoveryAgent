"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ChevronDown, LoaderCircle, Search, TriangleAlert } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { SOURCE_META } from "@/components/app/badges";
import { api, ApiError } from "@/lib/api";
import type { IdeaInput, SourceSystem } from "@/lib/types";
import { cn } from "@/lib/utils";

const ALL_SOURCES = Object.keys(SOURCE_META) as SourceSystem[];

export function IdeaForm({ initial, compact = false }: { initial?: Partial<IdeaInput>; compact?: boolean }) {
  const router = useRouter();
  const [idea, setIdea] = useState<IdeaInput>({ description: "", ...initial });
  const [sources, setSources] = useState<SourceSystem[]>(ALL_SOURCES);
  const [failures, setFailures] = useState<SourceSystem[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tooShort = idea.description.trim().length < 10;

  const set = (k: keyof IdeaInput) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setIdea((s) => ({ ...s, [k]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (tooShort || sources.length === 0) return;
    setSubmitting(true);
    setError(null);
    const clean = Object.fromEntries(Object.entries(idea).map(([k, v]) => [k, typeof v === "string" && v.trim() === "" ? null : v])) as unknown as IdeaInput;
    try {
      const res = await api.startAnalysis({
        idea: clean,
        sources: sources.length === ALL_SOURCES.length ? null : sources,
        simulate_failures: failures,
      });
      router.push(`/analysis/${res.id}`);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Could not start the analysis.";
      setError(msg);
      toast.error(msg);
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4" aria-describedby={error ? "idea-form-error" : undefined}>
      <div className="space-y-1.5">
        <Label htmlFor="description" className="text-sm font-medium">
          Describe your idea <span className="text-red-600" aria-hidden>*</span>
        </Label>
        <Textarea
          id="description"
          required
          value={idea.description}
          onChange={set("description")}
          rows={compact ? 3 : 5}
          placeholder="e.g. We want to build an AI-powered cybersecurity checker that scans internal repositories for vulnerabilities and recommends fixes."
          className="resize-y bg-white text-[15px] leading-relaxed"
          maxLength={5000}
        />
        <p className="text-xs text-muted-foreground">Plain English is fine. Only this field is required.</p>
      </div>

      {!compact && (
        <Collapsible>
          <CollapsibleTrigger className="group flex items-center gap-1 text-sm font-medium text-primary">
            <ChevronDown className="size-4 transition-transform group-data-[state=open]:rotate-180" aria-hidden />
            Add more detail (optional)
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-3 grid gap-3 sm:grid-cols-2">
            <Field id="title" label="Idea title" value={idea.title} onChange={set("title")} />
            <Field id="department" label="Team / department" value={idea.department} onChange={set("department")} />
            <Field id="business_problem" label="Business problem" value={idea.business_problem} onChange={set("business_problem")} textarea />
            <Field id="proposed_functionality" label="Proposed functionality" value={idea.proposed_functionality} onChange={set("proposed_functionality")} textarea />
            <Field id="target_users" label="Target users" value={idea.target_users} onChange={set("target_users")} placeholder="e.g. developers, security engineers" />
            <Field id="technologies" label="Technologies being considered" value={idea.technologies} onChange={set("technologies")} placeholder="e.g. Python, LLM, GitHub Actions" />
          </CollapsibleContent>
        </Collapsible>
      )}

      {!compact && (
        <fieldset className="rounded-lg border bg-white p-4">
          <legend className="px-1 text-sm font-medium">Sources to search</legend>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {ALL_SOURCES.map((s) => {
              const meta = SOURCE_META[s];
              const Icon = meta.icon;
              const checked = sources.includes(s);
              return (
                <label key={s} className={cn("flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm", checked ? "border-primary/40 bg-secondary" : "bg-white")}>
                  <Checkbox checked={checked} onCheckedChange={(v) => setSources((cur) => (v ? [...cur, s] : cur.filter((x) => x !== s)))} />
                  <Icon className="size-4 text-primary" aria-hidden />
                  {meta.label}
                </label>
              );
            })}
          </div>
          {sources.length === 0 && <p className="mt-2 text-xs text-red-700">Select at least one source.</p>}
          <Collapsible className="mt-3">
            <CollapsibleTrigger className="group flex items-center gap-1 text-xs font-medium text-muted-foreground">
              <ChevronDown className="size-3.5 transition-transform group-data-[state=open]:rotate-180" aria-hidden />
              Resilience demo: simulate a source outage
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2 flex flex-wrap gap-2">
              {ALL_SOURCES.filter((s) => s !== "idea_registry").map((s) => (
                <label key={s} className="flex items-center gap-1.5 rounded border bg-amber-50/60 px-2 py-1 text-xs">
                  <Checkbox checked={failures.includes(s)} onCheckedChange={(v) => setFailures((cur) => (v ? [...cur, s] : cur.filter((x) => x !== s)))} />
                  <TriangleAlert className="size-3 text-amber-700" aria-hidden /> {SOURCE_META[s].label} unavailable
                </label>
              ))}
            </CollapsibleContent>
          </Collapsible>
        </fieldset>
      )}

      {error && (
        <p id="idea-form-error" role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <Button type="submit" size="lg" disabled={submitting || tooShort || sources.length === 0} className="w-full sm:w-auto">
        {submitting ? <LoaderCircle className="size-4 animate-spin" aria-hidden /> : <Search className="size-4" aria-hidden />}
        {submitting ? "Starting analysis…" : "Check for existing work"}
      </Button>
    </form>
  );
}

function Field(props: { id: string; label: string; value?: string | null; onChange: React.ChangeEventHandler<HTMLInputElement | HTMLTextAreaElement>; textarea?: boolean; placeholder?: string }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={props.id} className="text-xs font-medium text-muted-foreground">
        {props.label}
      </Label>
      {props.textarea ? (
        <Textarea id={props.id} value={props.value ?? ""} onChange={props.onChange} rows={2} className="bg-white" placeholder={props.placeholder} />
      ) : (
        <Input id={props.id} value={props.value ?? ""} onChange={props.onChange} className="bg-white" placeholder={props.placeholder} />
      )}
    </div>
  );
}
