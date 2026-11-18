"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { CircleCheck } from "lucide-react";
import { PageHeader } from "@/components/app/app-shell";
import { IdeaForm } from "@/components/app/idea-form";
import { Card, CardContent } from "@/components/ui/card";

function SubmitInner() {
  const params = useSearchParams();
  const description = params.get("q") ?? "";
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <Card>
        <CardContent className="pt-6">
          <IdeaForm initial={{ description }} />
        </CardContent>
      </Card>
      <aside className="space-y-4 text-sm">
        <Card className="bg-[var(--brand-navy)] text-blue-50">
          <CardContent className="space-y-3 pt-6">
            <p className="font-semibold text-white">What happens next</p>
            {[
              "Your idea is analysed for its objective, capabilities, users and alternative terminology.",
              "Each selected source is searched at the same time, using keyword and semantic search.",
              "Records that refer to the same initiative are grouped together, using cross-references between them.",
              "Each initiative is scored on 5 overlap dimensions, and you get evidence and next steps.",
            ].map((t) => (
              <p key={t} className="flex gap-2">
                <CircleCheck className="mt-0.5 size-4 shrink-0 text-blue-200" aria-hidden />
                {t}
              </p>
            ))}
          </CardContent>
        </Card>
        <p className="text-xs text-muted-foreground">
          The idea isn&apos;t registered or shared until you choose to register it. Searches are logged for audit purposes.
        </p>
      </aside>
    </div>
  );
}

export default function SubmitPage() {
  return (
    <>
      <PageHeader eyebrow="Step 1" title="Check an idea before you build it" description="Describe what you want to build. Idea Discovery searches internal systems for existing or similar work." />
      <Suspense>
        <SubmitInner />
      </Suspense>
    </>
  );
}
