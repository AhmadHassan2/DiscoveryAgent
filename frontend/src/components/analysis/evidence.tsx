"use client";

import { ExternalLink, Link2, Search } from "lucide-react";
import { useState } from "react";
import { FactLabel, SourceBadge } from "@/components/app/badges";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import type { EvidenceItem } from "@/lib/types";
import { formatDate, relativeDays } from "@/lib/utils";

export function EvidenceList({ items, max }: { items: EvidenceItem[]; max?: number }) {
  const [open, setOpen] = useState<EvidenceItem | null>(null);
  const [showAll, setShowAll] = useState(false);
  const visible = showAll || !max ? items : items.slice(0, max);
  return (
    <>
      <ul className="divide-y rounded-lg border bg-white">
        {visible.map((e) => (
          <li key={e.record_id}>
            <button onClick={() => setOpen(e)} className="flex w-full items-start gap-3 px-3 py-2.5 text-left hover:bg-muted">
              <SourceBadge source={e.source} className="mt-0.5 w-36 shrink-0 justify-start" />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-[var(--brand-navy)]">{e.title}</span>
                <span className="flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
                  <span className="font-mono">{e.external_key}</span>
                  {e.source_status && <span>· {e.source_status}</span>}
                  <span>· updated {relativeDays(e.updated_at)}</span>
                </span>
              </span>
              {e.matched ? (
                <span className="inline-flex shrink-0 items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-800" title={e.match_reason ?? ""}>
                  <Search className="size-3" aria-hidden /> Retrieved
                </span>
              ) : (
                <span className="inline-flex shrink-0 items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-900" title={e.link_reason ?? ""}>
                  <Link2 className="size-3" aria-hidden /> Linked
                </span>
              )}
            </button>
          </li>
        ))}
      </ul>
      {max && items.length > max && (
        <button onClick={() => setShowAll((v) => !v)} className="mt-1.5 text-xs font-medium text-primary">
          {showAll ? "Show fewer" : `Show all ${items.length} records`}
        </button>
      )}
      <RecordSheet item={open} onClose={() => setOpen(null)} />
    </>
  );
}

export function RecordSheet({ item, onClose }: { item: EvidenceItem | null; onClose: () => void }) {
  return (
    <Sheet open={!!item} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
        {item && (
          <>
            <SheetHeader>
              <div className="flex flex-wrap items-center gap-2">
                <SourceBadge source={item.source} />
                <FactLabel kind="fact" />
              </div>
              <SheetTitle className="text-[var(--brand-navy)]">{item.title}</SheetTitle>
              <SheetDescription className="font-mono text-xs">{item.external_key} · {item.record_type.replaceAll("_", " ")}</SheetDescription>
            </SheetHeader>
            <div className="space-y-4 px-4 pb-6 text-sm">
              <dl className="grid grid-cols-[120px_1fr] gap-y-1.5">
                <dt className="text-muted-foreground">Status</dt><dd>{item.source_status ?? "—"}</dd>
                <dt className="text-muted-foreground">Owner / author</dt><dd>{item.owner ?? item.author ?? "—"}</dd>
                <dt className="text-muted-foreground">Last updated</dt><dd>{formatDate(item.updated_at)} ({relativeDays(item.updated_at)})</dd>
              </dl>
              <div className="rounded-md border bg-muted p-3 leading-relaxed whitespace-pre-wrap">{item.snippet}</div>
              <div className="space-y-1 rounded-md border border-dashed p-3 text-xs">
                <p className="font-semibold text-[var(--brand-navy)]">Why this record is here</p>
                {item.matched ? <p>{item.match_reason}</p> : <p>Not directly retrieved. Pulled in through a cross-reference.</p>}
                {item.link_reason && <p>Linked to the initiative because it: {item.link_reason.charAt(0).toLowerCase() + item.link_reason.slice(1)}.</p>}
              </div>
              <a href={item.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm font-medium text-primary underline-offset-2 hover:underline">
                Open in {item.source_label} <ExternalLink className="size-3.5" aria-hidden />
              </a>
              <p className="text-xs text-muted-foreground">Links point to a fictional <code>.example</code> domain and do not resolve in this proof of concept.</p>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
