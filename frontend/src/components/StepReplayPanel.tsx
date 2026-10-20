import type { ReplayResponse } from "../lib/types";
import { policyLabel } from "../lib/chartHelpers";

interface Props {
  replay: ReplayResponse | null;
}

export function StepReplayPanel({ replay }: Props) {
  if (!replay) return null;

  return (
    <section className="rounded-xl border border-lab-border bg-lab-panel p-6">
      <h2 className="text-lg font-medium text-white">Step replay — {policyLabel(replay.policy)}</h2>
      <p className="mt-1 text-sm text-lab-muted">
        One request: prompt {replay.request.prompt_length} tok, output {replay.request.output_tokens} tok.{" "}
        {replay.completed ? "Completed." : "Truncated at step limit."}
      </p>
      <div className="mt-4 max-h-96 overflow-auto rounded-lg border border-lab-border">
        <table className="w-full min-w-[720px] text-left text-xs">
          <thead className="sticky top-0 bg-lab-bg text-lab-muted">
            <tr>
              <th className="p-2">Step</th>
              <th className="p-2">Seq len</th>
              <th className="p-2">Draft</th>
              <th className="p-2">Acc / Rej</th>
              <th className="p-2">Bonus</th>
              <th className="p-2">Out tok</th>
              <th className="p-2">Cost</th>
              <th className="p-2">Left</th>
            </tr>
          </thead>
          <tbody>
            {replay.steps.map((s) => (
              <tr key={s.step} className="border-t border-lab-border/40 font-mono text-slate-300">
                <td className="p-2">{s.step}</td>
                <td className="p-2">{s.sequence_length}</td>
                <td className="p-2">{s.draft_length || "—"}</td>
                <td className="p-2">
                  {s.draft_length ? `${s.draft_accepted} / ${s.draft_rejected}` : "—"}
                </td>
                <td className="p-2">{s.bonus_tokens}</td>
                <td className="p-2 text-lab-accent">{s.tokens_produced}</td>
                <td className="p-2">{s.execution_cost.toFixed(3)}</td>
                <td className="p-2">{s.remaining_tokens}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
