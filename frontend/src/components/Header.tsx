export function Header() {
  return (
    <header className="border-b border-lab-border bg-lab-panel/80 backdrop-blur">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <p className="mb-2 inline-block rounded border border-lab-warn/40 bg-lab-warn/10 px-3 py-1 font-mono text-xs uppercase tracking-wider text-lab-warn">
          Simulated results — not real GPU benchmarks
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-white">Speculation Budget Lab</h1>
        <p className="mt-2 max-w-3xl text-lab-muted">
          Exploring the throughput–latency trade-off in speculative decoding.
        </p>
        <div className="mt-6 grid gap-4 text-sm text-slate-300 md:grid-cols-3">
          <div className="rounded-lg border border-lab-border bg-lab-bg/60 p-4">
            <h2 className="font-medium text-white">Standard autoregressive</h2>
            <p className="mt-1 text-lab-muted">One target-model step per token. Baseline for latency and cost.</p>
          </div>
          <div className="rounded-lg border border-lab-border bg-lab-bg/60 p-4">
            <h2 className="font-medium text-white">Fixed-length speculative</h2>
            <p className="mt-1 text-lab-muted">
              Draft model proposes a fixed number of tokens; target verifies in one step.
            </p>
          </div>
          <div className="rounded-lg border border-lab-border bg-lab-bg/60 p-4">
            <h2 className="font-medium text-white">Adaptive speculation</h2>
            <p className="mt-1 text-lab-muted">
              Chooses draft length from estimated acceptance and cost (simplified vs production DSpark / DeepInfer).
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
