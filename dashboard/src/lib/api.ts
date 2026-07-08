// Typed API client for the AgentReplay backend.
// Types mirror specs/001-agentreplay-v1/contracts/api.openapi.yaml exactly —
// do not add/rename/drop fields without updating that contract first.

export type RunStatus = "running" | "completed" | "failed" | "flagged";
export type StepType = "llm_call" | "tool_call" | "state_change";

export interface Step {
  id: string;
  run_id: string;
  seq: number;
  type: StepType;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  latency_ms: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
  created_at: string | null;
}

export interface Contradiction {
  user_intent: string;
  agent_action: string;
}

export interface DetectionVerdict {
  verdict: "pass" | "fail";
  reason: string;
  contradiction: Contradiction | null;
}

export interface AnalysisVerdict {
  failing_step: number;
  root_cause: string;
  suggested_fix: string;
}

export interface RunMetadata {
  channel?: string;
  business_id?: string;
  detection?: DetectionVerdict;
  analysis?: AnalysisVerdict;
  [key: string]: unknown;
}

export interface Run {
  id: string;
  agent_id: string;
  session_id: string;
  status: RunStatus;
  parent_run_id: string | null;
  fork_step: number | null;
  run_metadata: RunMetadata;
  started_at: string | null;
  ended_at: string | null;
}

export interface RunDetail extends Run {
  steps: Step[]; // ordered by seq ascending
}

export interface ForkRequest {
  fork_step: number;
  modification: { system_prompt?: string; [key: string]: unknown };
  temperature?: number | null;
}

export interface SweepResult {
  run_id: string;
  detection: DetectionVerdict | null;
  status_after: RunStatus;
  error?: string | null;
}

export interface ApiError {
  detail: string;
}

// Server-rendered pages (Server Components) run inside the frontend
// container, where "localhost" resolves to that container, not the backend
// one — they need the Docker network hostname. Browser-side calls (from
// "use client" components) need the externally-reachable URL instead.
// API_BASE_URL_INTERNAL is deliberately NOT NEXT_PUBLIC_-prefixed so it's
// only ever read server-side and never leaks into the client bundle.
function resolveApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return (
      process.env.API_BASE_URL_INTERNAL ??
      process.env.NEXT_PUBLIC_API_BASE_URL ??
      "http://localhost:8000"
    );
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

const API_KEY = process.env.NEXT_PUBLIC_AGENTREPLAY_API_KEY ?? "";

class ApiRequestError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`API error ${status}: ${detail}`);
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${resolveApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_KEY}`,
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as ApiError;
      detail = body.detail ?? detail;
    } catch {
      // response body wasn't JSON — fall back to statusText
    }
    throw new ApiRequestError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export function listRuns(params?: {
  agent_id?: string;
  session_id?: string;
  status?: RunStatus;
  limit?: number;
  offset?: number;
}): Promise<Run[]> {
  const query = new URLSearchParams();
  if (params?.agent_id) query.set("agent_id", params.agent_id);
  if (params?.session_id) query.set("session_id", params.session_id);
  if (params?.status) query.set("status", params.status);
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  const qs = query.toString();
  return request<Run[]>(`/runs${qs ? `?${qs}` : ""}`);
}

export function getRun(runId: string): Promise<RunDetail> {
  return request<RunDetail>(`/runs/${runId}`);
}

export function forkRun(
  runId: string,
  body: ForkRequest,
): Promise<RunDetail> {
  return request<RunDetail>(`/runs/${runId}/fork`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function analyzeRun(runId: string): Promise<AnalysisVerdict> {
  return request<AnalysisVerdict>(`/runs/${runId}/analyze`, {
    method: "POST",
  });
}

export function detectSweep(runIds?: string[]): Promise<SweepResult[]> {
  return request<SweepResult[]>(`/detect/sweep`, {
    method: "POST",
    body: JSON.stringify(runIds ? { run_ids: runIds } : {}),
  });
}

export { ApiRequestError };
