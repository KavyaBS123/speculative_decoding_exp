import type { ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ConcurrencySweepPoint, ExperimentResponse } from "../lib/types";
import { POLICY_COLORS, policyLabel } from "../lib/chartHelpers";

interface Props {
  experiment: ExperimentResponse | null;
  concurrencySeries: ConcurrencySweepPoint[] | null;
  acceptanceSeries: { base_acceptance: number; policy: string; throughput_tokens_per_sec: number }[] | null;
  fixedCompare:
    | {
        fixed_draft_length: number;
        fixed_throughput: number;
        adaptive_throughput: number;
        fixed_rejected: number;
        adaptive_rejected: number;
      }[]
    | null;
}

function throughputByConcurrency(series: ConcurrencySweepPoint[]) {
  const concurrencies = [...new Set(series.map((s) => s.concurrency))].sort((a, b) => a - b);
  return concurrencies.map((c) => {
    const row: Record<string, number | string> = { concurrency: c };
    for (const s of series.filter((x) => x.concurrency === c)) {
      row[s.policy] = s.throughput_tokens_per_sec;
    }
    return row;
  });
}

function latencyThroughput(series: ConcurrencySweepPoint[]) {
  return series.map((s) => ({
    policy: s.policy,
    throughput: s.throughput_tokens_per_sec,
    mean_latency: s.mean_latency,
    p95_latency: s.p95_latency,
  }));
}

export function ChartsPanel({ experiment, concurrencySeries, acceptanceSeries, fixedCompare }: Props) {
  if (!experiment && !concurrencySeries) {
    return (
      <section className="rounded-xl border border-dashed border-lab-border p-8 text-center text-lab-muted">
        Charts populate after you run an experiment or sweep.
      </section>
    );
  }

  const draftCurve = experiment?.charts.draft_length_vs_useful ?? [];
  const wasted = experiment?.charts.wasted_verification;
  const wastedData = wasted
    ? [
        { name: "Fixed", accepted: wasted.fixed.accepted, rejected: wasted.fixed.rejected },
        { name: "Adaptive", accepted: wasted.adaptive.accepted, rejected: wasted.adaptive.rejected },
      ]
    : [];

  const concData = concurrencySeries ? throughputByConcurrency(concurrencySeries) : [];
  const ltFromSweep = concurrencySeries ? latencyThroughput(concurrencySeries) : [];
  const ltFromExperiment = experiment
    ? Object.entries(experiment.results).map(([policy, r]) => ({
        policy,
        throughput: r.throughput_tokens_per_sec,
        mean_latency: r.mean_latency,
        p95_latency: r.p95_latency,
      }))
    : [];
  const ltData = ltFromSweep.length > 0 ? ltFromSweep : ltFromExperiment;

  const accData = acceptanceSeries
    ? [...new Set(acceptanceSeries.map((s) => s.base_acceptance))]
        .sort((a, b) => a - b)
        .map((a) => {
          const row: Record<string, number | string> = { base_acceptance: a };
          acceptanceSeries.filter((s) => s.base_acceptance === a).forEach((s) => {
            row[s.policy] = s.throughput_tokens_per_sec;
          });
          return row;
        })
    : [];

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {concData.length > 0 && (
        <ChartCard title="Throughput vs concurrency" subtitle="tok/s across parallel slots">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={concData}>
              <CartesianGrid stroke="#1e2a38" />
              <XAxis dataKey="concurrency" label={{ value: "Concurrency", position: "insideBottom", offset: -4 }} />
              <YAxis label={{ value: "tok/s", angle: -90, position: "insideLeft" }} />
              <Tooltip />
              <Legend />
              {["standard", "fixed_speculative", "adaptive"].map((p) => (
                <Line key={p} type="monotone" dataKey={p} name={policyLabel(p)} stroke={POLICY_COLORS[p]} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {ltData.length > 0 && (
        <ChartCard title="Latency vs throughput" subtitle="Mean latency (cost-time) vs tok/s">
          <ResponsiveContainer width="100%" height={280}>
            <ScatterChart>
              <CartesianGrid stroke="#1e2a38" />
              <XAxis type="number" dataKey="throughput" name="Throughput" unit=" tok/s" />
              <YAxis type="number" dataKey="mean_latency" name="Mean latency" />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} />
              <Legend />
              {["standard", "fixed_speculative", "adaptive"].map((p) => (
                <Scatter
                  key={p}
                  name={policyLabel(p)}
                  data={ltData.filter((d) => d.policy === p)}
                  fill={POLICY_COLORS[p]}
                />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {draftCurve.length > 0 && (
        <ChartCard
          title="Draft length vs useful tokens"
          subtitle="Expected accepted tokens (analytic); longer drafts are not always better"
        >
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={draftCurve}>
              <CartesianGrid stroke="#1e2a38" />
              <XAxis dataKey="draft_length" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="expected_accepted" name="E[accepted]" stroke="#60a5fa" />
              <Line type="monotone" dataKey="expected_with_bonus" name="E[accepted + bonus]" stroke="#3dd6c3" />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {wastedData.length > 0 && (
        <ChartCard title="Wasted verification" subtitle="Accepted vs rejected draft tokens">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={wastedData}>
              <CartesianGrid stroke="#1e2a38" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="accepted" stackId="a" fill="#3dd6c3" name="Accepted" />
              <Bar dataKey="rejected" stackId="a" fill="#f87171" name="Rejected" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {accData.length > 0 && (
        <ChartCard title="Acceptance probability sensitivity" subtitle="Throughput vs base acceptance">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={accData}>
              <CartesianGrid stroke="#1e2a38" />
              <XAxis dataKey="base_acceptance" />
              <YAxis label={{ value: "tok/s", angle: -90, position: "insideLeft" }} />
              <Tooltip />
              <Legend />
              {["standard", "fixed_speculative", "adaptive"].map((p) => (
                <Line key={p} type="monotone" dataKey={p} name={policyLabel(p)} stroke={POLICY_COLORS[p]} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {fixedCompare && fixedCompare.length > 0 && (
        <ChartCard title="Fixed draft length vs adaptive" subtitle="Throughput by fixed length (same seed workload per row)">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={fixedCompare}>
              <CartesianGrid stroke="#1e2a38" />
              <XAxis dataKey="fixed_draft_length" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="fixed_throughput" name="Fixed policy" stroke="#60a5fa" />
              <Line type="monotone" dataKey="adaptive_throughput" name="Adaptive (same run config)" stroke="#3dd6c3" />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      )}
    </div>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-lab-border bg-lab-panel p-4">
      <h3 className="font-medium text-white">{title}</h3>
      <p className="text-xs text-lab-muted">{subtitle}</p>
      <div className="mt-3">{children}</div>
    </section>
  );
}
