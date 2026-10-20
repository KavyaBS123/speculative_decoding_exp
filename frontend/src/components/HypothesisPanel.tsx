import { useState } from "react";
import { checkHypothesis } from "../lib/api";
import type { ExperimentParams, HypothesisEvaluation } from "../lib/types";

interface Props {
  params: ExperimentParams;
}

export function HypothesisPanel({ params }: Props) {
  const [text, setText] = useState("adaptive beats fixed on throughput");
  const [result, setResult] = useState<HypothesisEvaluation | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const { evaluation } = await checkHypothesis(params, text);
      setResult(evaluation);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-xl border border-lab-border bg-lab-panel p-6">
      <h2 className="text-lg font-medium text-white">Hypothesis check</h2>
      <p className="mt-1 text-sm text-lab-muted">
        Runs one experiment and tests a plain-language claim against the results.
      </p>
      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <input
          className="flex-1 rounded-md border border-lab-border bg-lab-bg px-3 py-2 text-sm text-slate-100"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. adaptive rejects less waste"
        />
        <button
          type="button"
          disabled={loading}
          onClick={run}
          className="rounded-md bg-lab-accent/90 px-4 py-2 text-sm font-medium text-lab-bg"
        >
          {loading ? "Checking…" : "Test hypothesis"}
        </button>
      </div>
      {result && (
        <div
          className={`mt-4 rounded-lg border px-4 py-3 text-sm ${
            result.supported === true
              ? "border-lab-accent/40 bg-lab-accent/10 text-lab-accent"
              : result.supported === false
                ? "border-red-500/40 bg-red-500/10 text-red-200"
                : "border-lab-border text-lab-muted"
          }`}
        >
          <p className="font-medium">{result.message}</p>
          <ul className="mt-2 list-disc pl-5 text-slate-300">
            {result.checks.map((c) => (
              <li key={c.id}>
                {c.passed ? "✓" : "✗"} {c.detail}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
