"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Bot, ChevronRight, Database, FlaskConical, History, LayoutDashboard, Library, Menu, Network, Search, TriangleAlert, X,
} from "lucide-react";
import { api } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

const NAV_GROUPS = [
  {
    label: "Validate",
    items: [
      { href: "/", label: "Home", icon: LayoutDashboard, exact: true },
      { href: "/submit", label: "Check an idea", icon: Search },
      { href: "/demo", label: "Demo scenarios", icon: FlaskConical },
    ],
  },
  {
    label: "Explore",
    items: [
      { href: "/registry", label: "Idea Registry", icon: Library },
      { href: "/sources", label: "Source Explorer", icon: Network },
      { href: "/history", label: "Search history", icon: History },
    ],
  },
];

// Content is left-aligned next to the sidebar (not centred) so wide or zoomed-out windows
// don't open a gap between the navigation and the page.
const CONTENT = "w-full max-w-[1400px] px-4 sm:px-8";

function isActive(pathname: string, href: string, exact?: boolean) {
  if (exact) return pathname === href;
  if (href === "/history") return pathname.startsWith("/history") || pathname.startsWith("/analysis");
  if (href === "/sources") return pathname.startsWith("/sources") || pathname.startsWith("/projects");
  return pathname.startsWith(href);
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-6 px-3 pt-5" aria-label="Main">
      {NAV_GROUPS.map((group) => (
        <div key={group.label}>
          <p className="px-3 pb-2 text-xs font-semibold tracking-wider text-blue-200/70 uppercase">{group.label}</p>
          <ul className="space-y-1">
            {group.items.map(({ href, label, icon: Icon, exact }) => {
              const active = isActive(pathname, href, exact);
              return (
                <li key={href}>
                  <Link
                    href={href}
                    onClick={onNavigate}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex min-h-11 items-center gap-3 rounded-lg px-3 text-[15px] transition-colors",
                      active ? "bg-white font-semibold text-[var(--brand-navy)] shadow-sm" : "text-blue-100 hover:bg-white/10 hover:text-white",
                    )}
                  >
                    <Icon className="size-[18px]" aria-hidden />
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

function Brand() {
  return (
    <Link href="/" className="block border-b border-white/10 px-6 py-5 leading-tight">
      <span className="block text-[17px] font-semibold tracking-tight text-white">Idea Discovery</span>
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <div className="flex min-h-screen bg-background">
      <aside className="no-print sticky top-0 hidden h-screen w-64 shrink-0 flex-col bg-sidebar lg:flex">
        <Brand />
        <NavLinks />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <div className="flex w-72 flex-col bg-sidebar pb-6">
            <div className="flex items-center justify-between pr-3">
              <Brand />
              <button onClick={() => setMobileOpen(false)} className="grid size-11 place-items-center rounded-lg text-white hover:bg-white/10" aria-label="Close navigation">
                <X className="size-5" />
              </button>
            </div>
            <NavLinks onNavigate={() => setMobileOpen(false)} />
          </div>
          <button className="flex-1 bg-black/40" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar onMenu={() => setMobileOpen(true)} />
        <main className={cn(CONTENT, "flex-1 py-8")}>{children}</main>
      </div>
    </div>
  );
}

function TopBar({ onMenu }: { onMenu: () => void }) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    api.health().then(setHealth).catch(() => setError(true));
  }, []);
  const llmLive = health && health.llm_provider !== "deterministic";
  return (
    <header className="no-print sticky top-0 z-30 border-b bg-white">
      <div className={cn(CONTENT, "flex h-16 items-center gap-3")}>
        <button onClick={onMenu} className="grid size-11 place-items-center rounded-lg text-[var(--brand-navy)] hover:bg-secondary lg:hidden" aria-label="Open navigation">
          <Menu className="size-5" />
        </button>
        <Link href="/submit" className="hidden h-10 items-center gap-2 rounded-lg border bg-background px-3 text-sm text-muted-foreground hover:border-[var(--brand-blue)] hover:text-[var(--brand-navy)] sm:flex sm:w-80">
          <Search className="size-4" aria-hidden /> Check a new idea…
        </Link>
        <div className="ml-auto flex items-center gap-2 text-xs">
          {error && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1.5 font-medium text-red-700 ring-1 ring-red-200">
              <TriangleAlert className="size-3.5" /> API offline
            </span>
          )}
          {health && health.failing_sources.length > 0 && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1.5 font-medium text-amber-900 ring-1 ring-amber-300">
              <TriangleAlert className="size-3.5" /> Outage: {health.failing_sources.join(", ")}
            </span>
          )}
          <span className="hidden items-center gap-1.5 rounded-full bg-secondary px-3 py-1.5 font-medium text-[var(--brand-navy)] md:inline-flex" title="Connectors are simulated and use synthetic data">
            <Database className="size-3.5" aria-hidden /> Mock data
          </span>
          {health && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--brand-navy)] px-3 py-1.5 font-medium text-white"
              title={llmLive ? `LLM: ${health.llm_provider} ${health.llm_model}` : "No LLM configured: deterministic analysis"}>
              <Bot className="size-3.5" aria-hidden /> {llmLive ? health.llm_model : "Demo AI mode"}
            </span>
          )}
        </div>
      </div>
    </header>
  );
}

export function Breadcrumbs({ items }: { items: { label: string; href?: string }[] }) {
  return (
    <nav aria-label="Breadcrumb" className="no-print mb-3">
      <ol className="flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
        {items.map((item, i) => (
          <li key={i} className="flex items-center gap-1">
            {i > 0 && <ChevronRight className="size-4 text-slate-400" aria-hidden />}
            {item.href ? (
              <Link href={item.href} className="rounded px-1 py-0.5 hover:bg-secondary hover:text-[var(--brand-navy)]">{item.label}</Link>
            ) : (
              <span className="max-w-[40ch] truncate px-1 font-medium text-[var(--brand-navy)]" aria-current="page">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export function PageHeader({ title, description, actions, eyebrow }: { title: string; description?: React.ReactNode; actions?: React.ReactNode; eyebrow?: string }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        {eyebrow && <p className="mb-1 text-sm font-medium text-[var(--brand-blue)]">{eyebrow}</p>}
        <h1 className="text-3xl font-semibold tracking-tight text-[var(--brand-navy)]">{title}</h1>
        {description && <p className="mt-2 max-w-3xl text-base leading-relaxed text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">
      <p className="font-semibold">Something went wrong</p>
      <p className="mt-1">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 rounded-lg bg-white px-3 py-2 font-medium ring-1 ring-red-200 hover:bg-red-100">
          Try again
        </button>
      )}
    </div>
  );
}
