import { useCallback, useEffect, useState } from "react";
import { Header } from "./components/Header";
import { ControlPanel } from "./components/ControlPanel";
import { MetricsPanel } from "./components/MetricsPanel";
import { InsightsPanel } from "./components/InsightsPanel";
import { ChartsPanel } from "./components/ChartsPanel";
import { PresetsPanel } from "./components/PresetsPanel";
import { HypothesisPanel } from "./components/HypothesisPanel";
import { BatchResultsPanel } from "./components/BatchResultsPanel";
import { StepReplayPanel } from "./components/StepReplayPanel";
import { CompareRunsPanel } from "./components/CompareRunsPanel";
import {
  compareFixedLengths,
  exportCsv,
  exportJson,
  fetchDefaults,
  fetchReplay,
  runBatch,
  runExperiment,
  sweepAcceptance,
  sweepConcurrency,
} from "./lib/api";
import type {
  BatchAggregates,
  ConcurrencySweepPoint,
  ExperimentParams,
  ExperimentResponse,
  ReplayResponse,
} from "./lib/types";

const CONCURRENCY_SWEEP = [1, 2, 4, 8, 16];
const ACCEPTANCE_SWEEP = [0.5, 0.65, 0.75, 0.85, 0.95];

export default function App() {
  const [params, setParams] = useState<ExperimentParams | null>(null);
  const [experiment, setExperiment] = useState<ExperimentResponse | null>(null);
  const [concurrencySeries, setConcurrencySeries] = useState<ConcurrencySweepPoint[] | null>(null);
  const [acceptanceSeries, setAcceptanceSeries] = useState<
    { base_acceptance: number; policy: string; throughput_tokens_per_sec: number }[] | null
  >(null);
  const [fixedCompare, setFixedCompare] = useState<
    | {
        fixed_draft_length: number;
        fixed_throughput: number;
        adaptive_throughput: number;
        fixed_rejected: number;
        adaptive_rejected: number;
      }[]
    | null
  >(null);
  const [batch, setBatch] = useState<BatchAggregates | null>(null);
  const [replay, setReplay] = useState<ReplayResponse | null>(null);
  const [batchNumSeeds, setBatchNumSeeds] = useState(5);
  const [replayPolicy, setReplayPolicy] = useState<"standard" | "fixed_speculative" | "adaptive">("adaptive");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDefaults()
      .then(setParams)
      .catch((e) => setError(String(e)));
  }, []);

  const onRun = useCallback(async () => {
    if (!params) return;
    setLoading(true);
    setError(null);
    try {
      const [exp, cmp] = await Promise.all([runExperiment(params), compareFixedLengths(params)]);
      setExperiment(exp);
      setFixedCompare(cmp.comparison);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [params]);

  const onReset = useCallback(async () => {
    setLoading(true);
    try {
      const d = await fetchDefaults();
      setParams(d);
      setExperiment(null);
      setConcurrencySeries(null);
      setAcceptanceSeries(null);
      setFixedCompare(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const onSweepConcurrency = useCallback(async () => {
    if (!params) return;
    setLoading(true);
    setError(null);
    try {
      const res = await sweepConcurrency(params, CONCURRENCY_SWEEP);
      setConcurrencySeries(res.series);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [params]);

  const onSweepAcceptance = useCallback(async () => {
    if (!params) return;
    setLoading(true);
    setError(null);
    try {
      const res = await sweepAcceptance(params, ACCEPTANCE_SWEEP);
      setAcceptanceSeries(res.series);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [params]);

  const onBatchRun = useCallback(async () => {
    if (!params) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runBatch(params, batchNumSeeds, 1);
      setBatch(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [params, batchNumSeeds]);

  const onLoadReplay = useCallback(async () => {
    if (!params) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchReplay(params, replayPolicy, 40);
      setReplay(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [params, replayPolicy]);

  const download = async (kind: "json" | "csv") => {
    if (!params) return;
    const res = kind === "json" ? await exportJson(params) : await exportCsv(params);
    const blob = new Blob([res.content], { type: kind === "json" ? "application/json" : "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `speculation-budget-lab.${kind}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!params) {
    return (
      <div className="min-h-screen bg-lab-bg p-8 text-slate-200">
        <Header />
        <main className="mx-auto mt-8 max-w-2xl space-y-4">
          {error ? (
            <>
              <div className="rounded border border-lab-warn/40 bg-lab-warn/10 px-4 py-3 text-sm">
                <p className="font-medium text-lab-warn">Backend not reachable</p>
                <p className="mt-2 text-slate-300">
                  The UI loads settings from <code className="text-lab-accent">http://127.0.0.1:8000</code>. Start the
                  API in a <strong>second terminal</strong>, then refresh this page.
                </p>
              </div>
              <pre className="overflow-x-auto rounded-lg border border-lab-border bg-lab-panel p-4 font-mono text-xs text-slate-300">
                {`cd /Users/kavya/Desktop/speculative_decoding
source .venv/bin/activate
cd backend
PYTHONPATH=. uvicorn api.main:app --reload --host 127.0.0.1 --port 8000`}
              </pre>
              <p className="text-sm text-lab-muted">Technical detail: {error}</p>
            </>
          ) : (
            <p className="text-lab-muted">Loading defaults…</p>
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-lab-bg">
      <Header />
      <main className="mx-auto max-w-7xl space-y-8 px-6 py-8">
        {error && (
          <div className="rounded border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</div>
        )}
        <PresetsPanel params={params} onApply={setParams} />
        <ControlPanel
          params={params}
          onChange={setParams}
          onRun={onRun}
          onReset={onReset}
          onSweepConcurrency={onSweepConcurrency}
          onSweepAcceptance={onSweepAcceptance}
          onBatchRun={onBatchRun}
          onLoadReplay={onLoadReplay}
          batchNumSeeds={batchNumSeeds}
          onBatchNumSeedsChange={setBatchNumSeeds}
          loading={loading}
        />
        <label className="-mt-4 block text-sm text-lab-muted">
          Step replay policy{" "}
          <select
            className="ml-2 rounded border border-lab-border bg-lab-panel px-2 py-1 text-slate-200"
            value={replayPolicy}
            onChange={(e) => setReplayPolicy(e.target.value as typeof replayPolicy)}
          >
            <option value="standard">Standard AR</option>
            <option value="fixed_speculative">Fixed speculative</option>
            <option value="adaptive">Adaptive</option>
          </select>
        </label>
        <MetricsPanel results={experiment?.results ?? null} />
        <BatchResultsPanel batch={batch} />
        <StepReplayPanel replay={replay} />
        <CompareRunsPanel params={params} experiment={experiment} />
        <HypothesisPanel params={params} />
        <InsightsPanel insights={experiment?.insights ?? null} />
        {experiment && (
          <div className="flex gap-3">
            <button
              type="button"
              className="rounded-md border border-lab-border px-3 py-2 text-sm"
              onClick={() => download("json")}
            >
              Export JSON
            </button>
            <button
              type="button"
              className="rounded-md border border-lab-border px-3 py-2 text-sm"
              onClick={() => download("csv")}
            >
              Export CSV
            </button>
          </div>
        )}
        <ChartsPanel
          experiment={experiment}
          concurrencySeries={concurrencySeries}
          acceptanceSeries={acceptanceSeries}
          fixedCompare={fixedCompare}
        />
      </main>
    </div>
  );
}
