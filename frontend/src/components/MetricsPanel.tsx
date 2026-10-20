import type { PolicyResult } from "../lib/types";
import { policyLabel } from "../lib/chartHelpers";

interface Props {
  results: Record<string, PolicyResult> | null;
}

const METRICS: { key: keyof PolicyResult; label: string; unit: string; fmt?: (v: number) => string }[] = [
  { key: "throughput_tokens_per_sec", label: "Throughput", unit: "tok/s", fmt: (v) => v.toFixed(2) },
  { key: "mean_latency", label: "Mean latency", unit: "cost-time", fmt: (v) => v.toFixed(3) },
  { key: "p95_latency", label: "P95 latency", unit: "cost-time", fmt: (v) => v.toFixed(3) },
  { key: "total_execution_cost", label: "Total execution cost", unit: "cost units", fmt: (v) => v.toFixed(2) },
  { key: "avg_accepted_per_verification", label: "Avg accepted / verification", unit: "tokens", fmt: (v) => v.toFixed(2) },
  { key: "draft_tokens_rejected", label: "Draft tokens rejected", unit: "tokens", fmt: (v) => String(Math.round(v)) },
  { key: "verification_operations", label: "Verification ops", unit: "count", fmt: (v) => String(Math.round(v)) },
  { key: "speculation_efficiency", label: "Speculation efficiency", unit: "tok / cost", fmt: (v) => v.toFixed(4) },
];

export function MetricsPanel({ results }: Props) {
  if (!results) {
    return (
      <section className="rounded-xl border border-dashed border-lab-border bg-lab-panel/50 p-8 text-center text-lab-muted">
        Run an experiment to see policy metrics. No prefilled benchmark numbers.
      </section>
    );
  }

  const policies = Object.keys(results);

  return (
    <section className="rounded-xl border border-lab-border bg-lab-panel p-6">
      <h2 className="text-lg font-medium text-white">Results summary</h2>
      <p className="mt-1 text-xs text-lab-muted">
        Latency uses simulated wall-clock time (parallel waves). Cost sums all decoding operations.
      </p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead>
            <tr className="border-b border-lab-border text-lab-muted">
              <th className="py-2 pr-4 font-medium">Metric</th>
              {policies.map((p) => (
                <th key={p} className="py-2 px-2 font-medium text-slate-200">
                  {policyLabel(p)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {METRICS.map((m) => (
              <tr key={m.key} className="border-b border-lab-border/60">
                <td className="py-2 pr-4 text-lab-muted">
                  {m.label} <span className="text-xs">({m.unit})</span>
                </td>
                {policies.map((p) => {
                  const val = results[p][m.key] as number;
                  return (
                    <td key={p} className="py-2 px-2 font-mono text-slate-100">
                      {m.fmt ? m.fmt(val) : val}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
