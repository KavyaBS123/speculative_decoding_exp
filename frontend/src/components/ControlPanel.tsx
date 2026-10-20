import type { ExperimentParams, WorkloadMode } from "../lib/types";

type FieldDef = {
  key: keyof ExperimentParams;
  label: string;
  help: string;
  type: "number" | "select";
  min?: number;
  max?: number;
  step?: number;
  options?: { value: string; label: string }[];
};

const FIELDS: FieldDef[] = [
  { key: "num_requests", label: "Number of requests", help: "How many generation requests are in the workload.", type: "number", min: 1, max: 256 },
  { key: "num_concurrent", label: "Parallel decoding slots", help: "How many requests run at once (affects verification batching).", type: "number", min: 1, max: 64 },
  { key: "fixed_draft_length", label: "Fixed draft length", help: "Tokens proposed per speculative step (fixed policy).", type: "number", min: 1, max: 8 },
  { key: "max_adaptive_draft_length", label: "Max adaptive draft length", help: "Upper cap for adaptive draft selection.", type: "number", min: 1, max: 8 },
  { key: "base_acceptance", label: "Base acceptance probability", help: "Chance the first draft token matches target verification.", type: "number", min: 0.01, max: 0.99, step: 0.01 },
  { key: "acceptance_decay", label: "Acceptance decay by position", help: "Multiplier applied per draft position (later tokens harder).", type: "number", min: 0.5, max: 1, step: 0.01 },
  { key: "draft_cost_per_token", label: "Draft model cost (per token)", help: "Simulated time/cost units for draft generation.", type: "number", min: 0.01, step: 0.01 },
  { key: "target_cost_per_token", label: "Target AR step cost", help: "Cost of one autoregressive target step.", type: "number", min: 0.01, step: 0.01 },
  { key: "verify_cost_base", label: "Verification cost (base)", help: "Target cost for one speculative verification op.", type: "number", min: 0.01, step: 0.01 },
  { key: "verify_efficiency_at_concurrency", label: "Verification efficiency (batched)", help: "Multiplier at high concurrency (<1 = cheaper verify when batched).", type: "number", min: 0.05, max: 1.5, step: 0.01 },
  { key: "saturation_concurrency", label: "Batch saturation point", help: "Concurrency where memory pressure begins.", type: "number", min: 1, max: 64 },
  { key: "memory_pressure_factor", label: "Memory pressure factor", help: "Extra verify cost growth beyond saturation.", type: "number", min: 0, step: 0.01 },
  { key: "output_tokens_per_request", label: "Output tokens per request", help: "Tokens each request must generate.", type: "number", min: 8, max: 4096 },
  { key: "prompt_length", label: "Prompt length (tokens)", help: "Input context size; affects sequence-length cost model.", type: "number", min: 8, max: 8192 },
  {
    key: "sequence_length_cost_scale",
    label: "Sequence-length cost scale",
    help: "Extra verify/AR cost per 1k prompt+generated tokens (0 = off).",
    type: "number",
    min: 0,
    max: 2,
    step: 0.05,
  },
  { key: "verification_budget", label: "Verification budget (0 = off)", help: "Max simulated cost per adaptive speculative step.", type: "number", min: 0, step: 0.1 },
  { key: "estimation_noise", label: "Acceptance estimate noise", help: "Std dev of error in adaptive acceptance estimates (0 = perfect).", type: "number", min: 0, max: 0.5, step: 0.01 },
  { key: "random_seed", label: "Random seed", help: "Fix seed to reproduce stochastic acceptance samples.", type: "number", min: 0 },
  {
    key: "workload_mode",
    label: "Workload mode",
    help: "Controlled = identical requests; Mixed = varied lengths and acceptance.",
    type: "select",
    options: [
      { value: "controlled", label: "Controlled experiment" },
      { value: "mixed", label: "Mixed workload" },
    ],
  },
];

interface Props {
  params: ExperimentParams;
  onChange: (p: ExperimentParams) => void;
  onRun: () => void;
  onReset: () => void;
  onSweepConcurrency: () => void;
  onSweepAcceptance: () => void;
  onBatchRun: () => void;
  onLoadReplay: () => void;
  batchNumSeeds: number;
  onBatchNumSeedsChange: (n: number) => void;
  loading: boolean;
}

export function ControlPanel({
  params,
  onChange,
  onRun,
  onReset,
  onSweepConcurrency,
  onSweepAcceptance,
  onBatchRun,
  onLoadReplay,
  batchNumSeeds,
  onBatchNumSeedsChange,
  loading,
}: Props) {
  const set = (key: keyof ExperimentParams, value: string) => {
    if (key === "workload_mode") {
      onChange({ ...params, workload_mode: value as WorkloadMode });
      return;
    }
    onChange({ ...params, [key]: Number(value) });
  };

  return (
    <section className="rounded-xl border border-lab-border bg-lab-panel p-6">
      <h2 className="text-lg font-medium text-white">Experiment controls</h2>
      <p className="mt-1 text-sm text-lab-muted">Adjust simulation parameters, then run. All metrics come from the engine.</p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FIELDS.map((f) => (
          <label key={f.key} className="block text-sm">
            <span className="font-medium text-slate-200">{f.label}</span>
            <span className="mt-0.5 block text-xs text-lab-muted">{f.help}</span>
            {f.type === "select" ? (
              <select
                className="mt-2 w-full rounded-md border border-lab-border bg-lab-bg px-3 py-2 text-slate-100"
                value={params[f.key] as string}
                onChange={(e) => set(f.key, e.target.value)}
              >
                {f.options?.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="number"
                className="mt-2 w-full rounded-md border border-lab-border bg-lab-bg px-3 py-2 font-mono text-sm text-slate-100"
                value={params[f.key] as number}
                min={f.min}
                max={f.max}
                step={f.step ?? 1}
                onChange={(e) => set(f.key, e.target.value)}
              />
            )}
          </label>
        ))}
      </div>
      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          disabled={loading}
          onClick={onRun}
          className="rounded-md bg-lab-accent px-4 py-2 text-sm font-medium text-lab-bg disabled:opacity-50"
        >
          {loading ? "Running…" : "Run experiment"}
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={onReset}
          className="rounded-md border border-lab-border px-4 py-2 text-sm text-slate-200"
        >
          Reset defaults
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={onSweepConcurrency}
          className="rounded-md border border-lab-border px-4 py-2 text-sm text-slate-200"
        >
          Concurrency sweep
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={onSweepAcceptance}
          className="rounded-md border border-lab-border px-4 py-2 text-sm text-slate-200"
        >
          Acceptance sweep
        </button>
        <label className="flex items-center gap-2 text-sm text-lab-muted">
          Batch seeds
          <input
            type="number"
            min={1}
            max={50}
            value={batchNumSeeds}
            onChange={(e) => onBatchNumSeedsChange(Number(e.target.value))}
            className="w-16 rounded border border-lab-border bg-lab-bg px-2 py-1 font-mono text-slate-100"
          />
        </label>
        <button
          type="button"
          disabled={loading}
          onClick={onBatchRun}
          className="rounded-md border border-lab-accent/50 px-4 py-2 text-sm text-lab-accent"
        >
          Multi-seed batch
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={onLoadReplay}
          className="rounded-md border border-lab-border px-4 py-2 text-sm text-slate-200"
        >
          Step replay
        </button>
      </div>
    </section>
  );
}
