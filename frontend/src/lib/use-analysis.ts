"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { AnalysisEnvelope, ProgressEvent } from "./types";

/** Loads an analysis and, while it runs, streams real backend progress events over SSE. */
export function useAnalysis(id: string) {
  const [envelope, setEnvelope] = useState<AnalysisEnvelope | null>(null);
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);

  const load = useCallback(async () => {
    try {
      const env = await api.analysis(id);
      setEnvelope(env);
      return env;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load analysis");
      return null;
    }
  }, [id]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const env = await load();
      if (!env || cancelled) return;
      if (env.status !== "running") {
        setEvents(env.events ?? []);
        return;
      }
      const es = new EventSource(api.eventsUrl(id));
      sourceRef.current = es;
      es.onmessage = (msg) => {
        const ev = JSON.parse(msg.data) as ProgressEvent;
        setEvents((cur) => (cur.some((c) => c.seq === ev.seq) ? cur : [...cur, ev]));
      };
      es.addEventListener("end", () => {
        es.close();
        void load();
      });
      es.onerror = () => {
        es.close();
        // Fall back to polling if the stream drops.
        const timer = setInterval(async () => {
          const e2 = await load();
          if (e2 && e2.status !== "running") {
            setEvents(e2.events ?? []);
            clearInterval(timer);
          }
        }, 1000);
      };
    })();
    return () => {
      cancelled = true;
      sourceRef.current?.close();
    };
  }, [id, load]);

  return { envelope, events, error, reload: load };
}
