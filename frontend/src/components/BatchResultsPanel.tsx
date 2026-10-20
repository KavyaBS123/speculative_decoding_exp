import { Bar, BarChart, CartesianGrid, ErrorBar, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { BatchAggregates } from "../lib/types";
import { POLICY_COLORS, policyLabel } from "../lib/chartHelpers";

interface Props {
  batch: BatchAggregates | null;
}

export function BatchResultsPanel({ batch }: Props) {
  if (!batch) return null;

  const data = Object.entries(batch.aggregates).map(([policy, metrics]) => ({
    policy: policyLabel(policy),
    policyKey: policy,
    mean: metrics.throughput_tokens_per_sec.mean,
    std: metrics.throughput_tokens_per_sec.std,
  }));

  return (
    <section className="rounded-xl border border-lab-border bg-lab-panel p-6">
      <h2 className="text-lg font-medium text-white">Multi-seed batch ({batch.num_seeds} seeds)</h2>
      <p className="mt-1 text-sm text-lab-muted">
        Throughput mean ± std across seeds {batch.seeds[0]}…{batch.seeds[batch.seeds.length - 1]} —{" "}
        {batch.disclaimer}
      </p>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="#1e2a38" />
            <XAxis dataKey="policy" />
            <YAxis label={{ value: "tok/s", angle: -90, position: "insideLeft" }} />
            <Tooltip formatter={(v: number) => v.toFixed(3)} />
            <Legend />
            <Bar dataKey="mean" name="Mean throughput" fill="#3dd6c3">
              <ErrorBar dataKey="std" width={4} stroke="#94a3b8" direction="y" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 overflow-x-auto text-xs">
        <table className="w-full text-left text-lab-muted">
          <thead>
            <tr>
              <th className="py-1">Policy</th>
              <th>Throughput μ±σ</th>
              <th>Rejected drafts μ±σ</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(batch.aggregates).map(([policy, m]) => (
              <tr key={policy} className="border-t border-lab-border/50 font-mono text-slate-300">
                <td className="py-1" style={{ color: POLICY_COLORS[policy] }}>
                  {policyLabel(policy)}
                </td>
                <td>
                  {m.throughput_tokens_per_sec.mean.toFixed(2)} ± {m.throughput_tokens_per_sec.std.toFixed(2)}
                </td>
                <td>
                  {m.draft_tokens_rejected.mean.toFixed(0)} ± {m.draft_tokens_rejected.std.toFixed(0)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
