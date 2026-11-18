import type {
  AnalysisEnvelope, AnalysisRequest, AnalysisSummary, Comparison, DemoScenario, GraphResponse, HealthResponse,
  IdeaInput, InitiativeDetail, InitiativeSummary, RegisteredIdea, RegistrationBlocked, SourceRecordRow, SourceSystem,
  SourcesOverview, StatsResponse,
} from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string, public body?: unknown) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, `Cannot reach the Idea Discovery API at ${API_URL}. Is the backend running?`);
  }
  const text = await res.text();
  const body = text ? safeJson(text) : null;
  if (!res.ok) {
    const detail = (body as { detail?: unknown })?.detail;
    const message = typeof detail === "string" ? detail : Array.isArray(detail) ? "Please check the form: some fields are invalid." : `Request failed (${res.status})`;
    throw new ApiError(res.status, message, body);
  }
  return body as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export const api = {
  health: () => request<HealthResponse>("/api/health"),
  stats: () => request<StatsResponse>("/api/stats"),
  startAnalysis: (body: AnalysisRequest) =>
    request<{ id: string; status: string; events_url: string; report_url: string }>("/api/analyses", { method: "POST", body: JSON.stringify(body) }),
  analysis: (id: string) => request<AnalysisEnvelope>(`/api/analyses/${id}`),
  analyses: (limit = 50) => request<AnalysisSummary[]>(`/api/analyses?limit=${limit}`),
  comparison: (id: string, initiativeId: string) => request<Comparison>(`/api/analyses/${id}/comparison/${encodeURIComponent(initiativeId)}`),
  exportUrl: (id: string) => `${API_URL}/api/analyses/${id}/export`,
  eventsUrl: (id: string) => `${API_URL}/api/analyses/${id}/events`,
  ideas: (q?: string) => request<RegisteredIdea[]>(`/api/ideas${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  registerIdea: (body: { idea: IdeaInput; submitted_by?: string; analysis_id?: string; acknowledge_overlap?: boolean; acknowledgement_note?: string }) =>
    request<RegisteredIdea>("/api/ideas", { method: "POST", body: JSON.stringify(body) }),
  sources: () => request<SourcesOverview>("/api/sources"),
  sourceRecords: (source: SourceSystem, q?: string) =>
    request<SourceRecordRow[]>(`/api/sources/${source}/records${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  projects: () => request<InitiativeSummary[]>("/api/projects"),
  project: (id: string) => request<InitiativeDetail>(`/api/projects/${id}`),
  graph: (includeRecords = true) => request<GraphResponse>(`/api/graph?include_records=${includeRecords}`),
  scenarios: () => request<DemoScenario[]>("/api/demo/scenarios"),
};

export function isRegistrationBlocked(e: unknown): e is ApiError & { body: RegistrationBlocked } {
  return e instanceof ApiError && e.status === 409 && typeof e.body === "object" && e.body !== null && "overlapping" in e.body;
}
