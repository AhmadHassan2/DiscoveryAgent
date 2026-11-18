import {
  Archive, Ban, BookOpen, CircleCheck, CircleDot, CirclePause, FlaskConical, FolderOpen, GitBranch, Hammer, Lightbulb,
  MessagesSquare, Rocket, Search, Server, Ticket, type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { LifecycleStage, OverlapCategory, SourceSystem } from "@/lib/types";

export const SOURCE_META: Record<SourceSystem, { label: string; icon: LucideIcon; tint: string }> = {
  confluence: { label: "Confluence", icon: BookOpen, tint: "bg-white text-[var(--brand-navy)] ring-slate-200" },
  jira: { label: "Jira", icon: Ticket, tint: "bg-white text-[var(--brand-navy)] ring-slate-200" },
  github: { label: "GitHub Enterprise", icon: GitBranch, tint: "bg-white text-[var(--brand-navy)] ring-slate-200" },
  sharepoint: { label: "SharePoint", icon: FolderOpen, tint: "bg-white text-[var(--brand-navy)] ring-slate-200" },
  teams: { label: "Microsoft Teams", icon: MessagesSquare, tint: "bg-white text-[var(--brand-navy)] ring-slate-200" },
  servicenow: { label: "ServiceNow", icon: Server, tint: "bg-white text-[var(--brand-navy)] ring-slate-200" },
  idea_registry: { label: "Idea Registry", icon: Lightbulb, tint: "bg-white text-[var(--brand-navy)] ring-slate-200" },
};

export function SourceBadge({ source, className, compact }: { source: SourceSystem; className?: string; compact?: boolean }) {
  const meta = SOURCE_META[source];
  const Icon = meta.icon;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset", meta.tint, className)}>
      <Icon className="size-3.5" aria-hidden />
      {compact ? null : meta.label}
      {compact ? <span className="sr-only">{meta.label}</span> : null}
    </span>
  );
}

export const CATEGORY_META: Record<OverlapCategory, { label: string; className: string; short: string }> = {
  near_duplicate: { label: "Near-duplicate", short: "Duplicate", className: "bg-[var(--cat-duplicate)] text-white" },
  strong_overlap: { label: "Strong overlap", short: "Strong", className: "bg-[var(--cat-strong)] text-white" },
  partial_overlap: { label: "Partial overlap", short: "Partial", className: "bg-white text-blue-800 ring-1 ring-inset ring-blue-400" },
  related: { label: "Related but different", short: "Related", className: "bg-[var(--brand-tint)] text-slate-700 ring-1 ring-inset ring-slate-200" },
  no_significant_match: { label: "No significant match", short: "No match", className: "bg-slate-100 text-slate-700 ring-1 ring-slate-300" },
};

export function CategoryBadge({ category, className, size = "sm" }: { category: OverlapCategory; className?: string; size?: "sm" | "lg" }) {
  const meta = CATEGORY_META[category];
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full font-semibold whitespace-nowrap", size === "lg" ? "px-3 py-1 text-sm" : "px-2 py-0.5 text-xs", meta.className, className)}>
      {meta.label}
    </span>
  );
}

const LIFECYCLE_META: Record<LifecycleStage, { label: string; icon: LucideIcon; className: string }> = {
  proposed: { label: "Proposed", icon: Lightbulb, className: "text-blue-900 bg-blue-50 ring-blue-200" },
  research: { label: "Research", icon: Search, className: "text-blue-900 bg-blue-50 ring-blue-200" },
  proof_of_concept: { label: "Proof of concept", icon: FlaskConical, className: "text-blue-900 bg-blue-50 ring-blue-200" },
  active_development: { label: "Active development", icon: Hammer, className: "text-blue-900 bg-blue-100 ring-blue-300" },
  deployed: { label: "Deployed", icon: Rocket, className: "text-white bg-[var(--brand-navy)] ring-[var(--brand-navy)]" },
  paused: { label: "Paused", icon: CirclePause, className: "text-slate-700 bg-white ring-slate-300" },
  abandoned: { label: "Abandoned", icon: Ban, className: "text-slate-700 bg-slate-100 ring-slate-300" },
  retired: { label: "Retired", icon: Archive, className: "text-slate-700 bg-slate-100 ring-slate-300" },
  unknown: { label: "Unknown", icon: CircleDot, className: "text-slate-600 bg-slate-50 ring-slate-200" },
};

export function LifecycleBadge({ stage, confidence, className }: { stage: LifecycleStage; confidence?: string; className?: string }) {
  const meta = LIFECYCLE_META[stage] ?? LIFECYCLE_META.unknown;
  const Icon = meta.icon;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset", meta.className, className)}>
      <Icon className="size-3.5" aria-hidden />
      {meta.label}
      {confidence ? <span className="font-normal opacity-70">· {confidence} confidence</span> : null}
    </span>
  );
}

export function FactLabel({ kind }: { kind: "fact" | "ai" | "rule" }) {
  const map = {
    fact: { text: "Retrieved fact", cls: "bg-white text-[var(--brand-navy)] ring-slate-300", icon: CircleCheck },
    ai: { text: "AI interpretation", cls: "bg-[var(--brand-navy)] text-white ring-[var(--brand-navy)]", icon: Lightbulb },
    rule: { text: "Rule-based interpretation", cls: "bg-slate-50 text-slate-700 ring-slate-300", icon: CircleDot },
  }[kind];
  const Icon = map.icon;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ring-inset", map.cls)}>
      <Icon className="size-3" aria-hidden /> {map.text}
    </span>
  );
}
