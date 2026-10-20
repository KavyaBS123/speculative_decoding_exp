import type {
  BatchAggregates,
  ExperimentParams,
  ExperimentResponse,
  HypothesisEvaluation,
  PresetInfo,
  ReplayResponse,
} from "./types";

const BASE = "/api";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  return res.json() as Promise<T>;
}

export async function fetchDefaults(): Promise<ExperimentParams> {
  const res = await fetch(`${BASE}/defaults`);
  if (!res.ok) throw new Error("Failed to load defaults");
  return res.json() as Promise<ExperimentParams>;
}

export function runExperiment(params: ExperimentParams) {
  return post<ExperimentResponse>("/experiment/run", params);
}

export function sweepConcurrency(params: ExperimentParams, values: number[]) {
  return post<{ series: import("./types").ConcurrencySweepPoint[] }>("/experiment/sweep/concurrency", {
    params,
    values,
  });
}

export function sweepAcceptance(params: ExperimentParams, values: number[]) {
  return post<{ series: { base_acceptance: number; policy: string; throughput_tokens_per_sec: number }[] }>(
    "/experiment/sweep/acceptance",
    { params, values },
  );
}

export function compareFixedLengths(params: ExperimentParams) {
  return post<{
    comparison: {
      fixed_draft_length: number;
      fixed_throughput: number;
      adaptive_throughput: number;
      fixed_rejected: number;
      adaptive_rejected: number;
    }[];
  }>("/experiment/compare/fixed-lengths", params);
}

export function exportJson(params: ExperimentParams) {
  return post<{ content: string }>("/export/json", params);
}

export function exportCsv(params: ExperimentParams) {
  return post<{ content: string }>("/export/csv", params);
}

export async function fetchPresets() {
  const res = await fetch(`${BASE}/presets`);
  if (!res.ok) throw new Error("Failed to load presets");
  return res.json() as Promise<{ presets: PresetInfo[] }>;
}

export function applyPreset(presetId: string, baseParams?: ExperimentParams) {
  return post<ExperimentParams>("/presets/apply", { preset_id: presetId, base_params: baseParams ?? null });
}

export function runBatch(params: ExperimentParams, numSeeds: number, seedStep: number) {
  return post<BatchAggregates>("/experiment/batch", { params, num_seeds: numSeeds, seed_step: seedStep });
}

export function fetchReplay(params: ExperimentParams, policy: string, maxSteps: number) {
  return post<ReplayResponse>("/experiment/replay", { params, policy, max_steps: maxSteps });
}

export function checkHypothesis(params: ExperimentParams, hypothesis: string) {
  return post<{ experiment: ExperimentResponse; evaluation: HypothesisEvaluation }>("/experiment/hypothesis", {
    params,
    hypothesis,
  });
}
