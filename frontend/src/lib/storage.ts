import type { ExperimentParams, ExperimentResponse } from "./types";

const KEY = "sbl_saved_runs_v1";

export interface SavedRun {
  id: string;
  label: string;
  savedAt: string;
  params: ExperimentParams;
  experiment: ExperimentResponse;
}

export function loadSavedRuns(): SavedRun[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    return JSON.parse(raw) as SavedRun[];
  } catch {
    return [];
  }
}

export function saveRun(label: string, params: ExperimentParams, experiment: ExperimentResponse): SavedRun[] {
  const runs = loadSavedRuns();
  const entry: SavedRun = {
    id: crypto.randomUUID(),
    label: label || `Run ${runs.length + 1}`,
    savedAt: new Date().toISOString(),
    params,
    experiment,
  };
  const next = [entry, ...runs].slice(0, 20);
  localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export function deleteSavedRun(id: string): SavedRun[] {
  const next = loadSavedRuns().filter((r) => r.id !== id);
  localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}
