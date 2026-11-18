"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ErrorState, PageHeader } from "@/components/app/app-shell";
import { CategoryBadge } from "@/components/app/badges";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import type { AnalysisSummary } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function HistoryPage() {
  const [rows, setRows] = useState<AnalysisSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.analyses(200).then(setRows).catch((e) => setError(e.message)); }, []);
  return (
    <>
      <PageHeader title="Search history" description="Every idea check is saved, so you can come back to previous validation reports. Searches are also written to the audit log." />
      {error && <ErrorState message={error} />}
      {rows === null ? <Skeleton className="h-64" /> : (
        <div className="overflow-x-auto rounded-lg border bg-white">
          <Table>
            <TableHeader><TableRow><TableHead>Idea</TableHead><TableHead>Result</TableHead><TableHead>Top match</TableHead><TableHead>AI mode</TableHead><TableHead>Date</TableHead></TableRow></TableHeader>
            <TableBody>
              {rows.length === 0 && <TableRow><TableCell colSpan={5} className="py-8 text-center text-muted-foreground">No searches yet.</TableCell></TableRow>}
              {rows.map((a) => (
                <TableRow key={a.id}>
                  <TableCell className="max-w-md"><Link href={`/analysis/${a.id}`} className="line-clamp-2 font-medium whitespace-normal text-[var(--brand-navy)] hover:text-primary">{a.title || a.idea_text}</Link>{a.scenario_id && <span className="text-xs text-muted-foreground">demo: {a.scenario_id}</span>}</TableCell>
                  <TableCell>{a.status === "completed" && a.top_category ? <CategoryBadge category={a.top_category} /> : <span className="text-xs text-muted-foreground">{a.status}</span>}</TableCell>
                  <TableCell className="text-sm">{a.top_initiative_name ?? "—"}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{a.capability_mode ?? "—"}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{formatDate(a.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </>
  );
}
