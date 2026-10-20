import { useEffect, useState } from "react";
import { applyPreset, fetchPresets } from "../lib/api";
import type { ExperimentParams, PresetInfo } from "../lib/types";

interface Props {
  params: ExperimentParams;
  onApply: (p: ExperimentParams) => void;
}

export function PresetsPanel({ params, onApply }: Props) {
  const [presets, setPresets] = useState<PresetInfo[]>([]);
  const [loading, setLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchPresets()
      .then((r) => setPresets(r.presets))
      .catch(() => setPresets([]));
  }, []);

  const load = async (id: string) => {
    setLoading(id);
    try {
      const next = await applyPreset(id, params);
      onApply(next);
    } finally {
      setLoading(null);
    }
  };

  return (
    <section className="rounded-xl border border-lab-border bg-lab-panel p-6">
      <h2 className="text-lg font-medium text-white">Experiment presets</h2>
      <p className="mt-1 text-sm text-lab-muted">One-click scenarios — still simulated, not real benchmarks.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {presets.map((p) => (
          <button
            key={p.id}
            type="button"
            disabled={loading === p.id}
            onClick={() => load(p.id)}
            className="rounded-lg border border-lab-border bg-lab-bg/60 p-4 text-left transition hover:border-lab-accent/40"
          >
            <span className="font-medium text-slate-100">{p.name}</span>
            <p className="mt-1 text-xs text-lab-muted">{p.description}</p>
          </button>
        ))}
      </div>
    </section>
  );
}
