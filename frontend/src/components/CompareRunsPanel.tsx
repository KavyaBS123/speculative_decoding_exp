import { useState } from "react";
import type { SavedRun } from "../lib/storage";
import { deleteSavedRun, loadSavedRuns, saveRun } from "../lib/storage";
import type { ExperimentParams, ExperimentResponse } from "../lib/types";
import { policyLabel } from "../lib/chartHelpers";

interface Props {
  params: ExperimentParams;
  experiment: ExperimentResponse | null;
}

function diffHighlight(a: number, b: number) {
  const d = b - a;
  const pct = a !== 0 ? (d / a) * 100 : 0;
  return `${d >= 0 ? "+" : ""}${d.toFixed(2)} (${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%)`;
}

export function CompareRunsPanel({ params, experiment }: Props) {
  const [runs, setRuns] = useState<SavedRun[]>(() => loadSavedRuns());
  const [label, setLabel] = useState("");
  const [aId, setAId] = useState("");
  const [bId, setBId] = useState("");

  const persist = (next: SavedRun[]) => {
    setRuns(next);
  };

  const onSave = () => {
    if (!experiment) return;
    persist(saveRun(label, params, experiment));
    setLabel("");
  };

  const runA = runs.find((r) => r.id === aId);
  const runB = runs.find((r) => r.id === bId);

  return (
    <section className="rounded-xl border border-lab-border bg-lab-panel p-6">
      <h2 className="text-lg font-medium text-white">Saved runs & compare</h2>
      <p className="mt-1 text-sm text-lab-muted">Stored in your browser (localStorage). Save after a run, then pick two to diff.</p>

      <div className="mt-4 flex flex-wrap gap-2">
        <input
          className="rounded border border-lab-border bg-lab-bg px-3 py-2 text-sm"
          placeholder="Label for current run"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />
        <button
          type="button"
          disabled={!experiment}
          onClick={onSave}
          className="rounded-md border border-lab-border px-3 py-2 text-sm disabled:opacity-40"
        >
          Save current run
        </button>
      </div>

      {runs.length > 0 && (
        <ul className="mt-4 space-y-2 text-sm">
          {runs.map((r) => (
            <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded border border-lab-border/60 px-3 py-2">
              <span>
                <strong className="text-slate-200">{r.label}</strong>
                <span className="ml-2 text-xs text-lab-muted">{new Date(r.savedAt).toLocaleString()}</span>
              </span>
              <button type="button" className="text-xs text-red-300" onClick={() => persist(deleteSavedRun(r.id))}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}

      {runs.length >= 2 && (
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <select className="rounded border border-lab-border bg-lab-bg p-2 text-sm" value={aId} onChange={(e) => setAId(e.target.value)}>
            <option value="">Run A…</option>
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))}
          </select>
          <select className="rounded border border-lab-border bg-lab-bg p-2 text-sm" value={bId} onChange={(e) => setBId(e.target.value)}>
            <option value="">Run B…</option>
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))}
          </select>
        </div>
      )}

      {runA && runB && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-lab-muted">
                <th className="py-2">Policy</th>
                <th className="py-2">A throughput</th>
                <th className="py-2">B throughput</th>
                <th className="py-2">Δ B vs A</th>
              </tr>
            </thead>
            <tbody>
              {(["standard", "fixed_speculative", "adaptive"] as const).map((p) => {
                const ta = runA.experiment.results[p]?.throughput_tokens_per_sec ?? 0;
                const tb = runB.experiment.results[p]?.throughput_tokens_per_sec ?? 0;
                return (
                  <tr key={p} className="border-t border-lab-border/50 font-mono">
                    <td className="py-2">{policyLabel(p)}</td>
                    <td>{ta.toFixed(2)}</td>
                    <td>{tb.toFixed(2)}</td>
                    <td className="text-lab-accent">{diffHighlight(ta, tb)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
