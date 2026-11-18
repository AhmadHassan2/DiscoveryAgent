"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { GraphResponse, GraphNode } from "@/lib/types";

const W = 1100;
const H = 720;
const COLORS: Record<GraphNode["type"], string> = {
  initiative: "#1d4ed8", team: "#2563eb", person: "#0f2a6b", record: "#93c5fd", idea: "#3b82f6",
};
const RADIUS: Record<GraphNode["type"], number> = { initiative: 9, team: 6, person: 5, record: 3.5, idea: 7 };

/** Deterministic force-directed layout (seeded positions, fixed iteration count). */
function layout(graph: GraphResponse) {
  const n = graph.nodes.length;
  const idx = new Map(graph.nodes.map((nd, i) => [nd.id, i]));
  const pos = graph.nodes.map((_, i) => {
    const a = (i / n) * Math.PI * 2 * 7.3;
    const r = 120 + ((i * 97) % 260);
    return { x: W / 2 + Math.cos(a) * r, y: H / 2 + Math.sin(a) * r, vx: 0, vy: 0 };
  });
  const edges = graph.edges.map((e) => [idx.get(e.source), idx.get(e.target)]).filter((e): e is [number, number] => e[0] != null && e[1] != null);
  for (let iter = 0; iter < 260; iter++) {
    const alpha = 1 - iter / 260;
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dx = pos[i].x - pos[j].x, dy = pos[i].y - pos[j].y;
        const d2 = dx * dx + dy * dy + 0.01;
        if (d2 > 40000) continue;
        const f = (420 * alpha) / d2;
        pos[i].vx += dx * f; pos[i].vy += dy * f; pos[j].vx -= dx * f; pos[j].vy -= dy * f;
      }
    }
    for (const [a, b] of edges) {
      const dx = pos[b].x - pos[a].x, dy = pos[b].y - pos[a].y;
      const d = Math.sqrt(dx * dx + dy * dy) || 1;
      const f = ((d - 38) / d) * 0.06 * alpha;
      pos[a].vx += dx * f; pos[a].vy += dy * f; pos[b].vx -= dx * f; pos[b].vy -= dy * f;
    }
    for (const p of pos) {
      p.vx += (W / 2 - p.x) * 0.004 * alpha; p.vy += (H / 2 - p.y) * 0.004 * alpha;
      p.x += Math.max(-20, Math.min(20, p.vx)); p.y += Math.max(-20, Math.min(20, p.vy));
      p.vx *= 0.55; p.vy *= 0.55;
      p.x = Math.max(16, Math.min(W - 16, p.x)); p.y = Math.max(16, Math.min(H - 16, p.y));
    }
  }
  return { pos, edges };
}

export function RelationshipGraph({ graph }: { graph: GraphResponse }) {
  const { pos, edges } = useMemo(() => layout(graph), [graph]);
  const [selected, setSelected] = useState<number | null>(null);
  const [hover, setHover] = useState<number | null>(null);
  const focus = hover ?? selected;
  const neighbours = useMemo(() => {
    if (focus == null) return null;
    const s = new Set([focus]);
    edges.forEach(([a, b]) => { if (a === focus) s.add(b); if (b === focus) s.add(a); });
    return s;
  }, [focus, edges]);
  const sel = selected != null ? graph.nodes[selected] : null;

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
      <div className="overflow-hidden rounded-lg border bg-white">
        <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label="Relationship graph of initiatives, teams, owners, ideas and source records">
          {edges.map(([a, b], i) => (
            <line key={i} x1={pos[a].x} y1={pos[a].y} x2={pos[b].x} y2={pos[b].y}
              stroke={neighbours && neighbours.has(a) && neighbours.has(b) ? "#1d4ed8" : "#cbd5e1"}
              strokeOpacity={neighbours ? (neighbours.has(a) && neighbours.has(b) ? 0.9 : 0.15) : 0.6} strokeWidth={neighbours && neighbours.has(a) && neighbours.has(b) ? 1.5 : 0.8} />
          ))}
          {graph.nodes.map((nd, i) => {
            const dim = neighbours && !neighbours.has(i);
            const showLabel = nd.type === "initiative" || nd.type === "idea" || (neighbours?.has(i) && nd.type !== "record") || i === focus;
            return (
              <g key={nd.id} transform={`translate(${pos[i].x},${pos[i].y})`} opacity={dim ? 0.2 : 1} className="cursor-pointer"
                onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} onClick={() => setSelected(i === selected ? null : i)}>
                <circle r={RADIUS[nd.type]} fill={COLORS[nd.type]} stroke={i === selected ? "#2563eb" : "#fff"} strokeWidth={i === selected ? 3 : 1.2} />
                {showLabel && <text x={RADIUS[nd.type] + 3} y={3.5} fontSize={nd.type === "initiative" ? 10.5 : 9.5} fill="#0f1d3d" fontWeight={nd.type === "initiative" ? 600 : 400}>{nd.label.length > 34 ? nd.label.slice(0, 33) + "…" : nd.label}</text>}
                <title>{`${nd.type}: ${nd.label}`}</title>
              </g>
            );
          })}
        </svg>
      </div>
      <aside className="space-y-4 text-sm">
        <div className="rounded-lg border bg-white p-4">
          <p className="mb-2 font-semibold text-[var(--brand-navy)]">Legend</p>
          <ul className="space-y-1.5">
            {(Object.keys(COLORS) as GraphNode["type"][]).map((t) => (
              <li key={t} className="flex items-center gap-2 capitalize"><span className="inline-block size-3 rounded-full" style={{ background: COLORS[t] }} />{t === "record" ? "Source record" : t === "idea" ? "Registered idea" : t}</li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">Hover over a node to highlight its connections, or click it to pin. Edges come only from source-native cross-references and ownership.</p>
        </div>
        {sel && (
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-muted-foreground capitalize">{sel.type}</p>
            <p className="font-semibold text-[var(--brand-navy)]">{sel.label}</p>
            {sel.group && <p className="text-xs text-muted-foreground">{sel.group}</p>}
            <p className="mt-1 text-xs">{neighbours ? neighbours.size - 1 : 0} connections</p>
            {sel.type === "initiative" && <Link href={`/projects/${sel.id}`} className="mt-2 inline-block text-xs font-medium text-primary hover:underline">Open initiative →</Link>}
          </div>
        )}
      </aside>
    </div>
  );
}
