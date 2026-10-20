# Speculation Budget Lab

Interactive **simulator** for comparing standard autoregressive decoding, fixed-length speculative decoding, and a simplified **adaptive** draft-length policy under configurable cost and acceptance models.

## Research question

**When does adaptive speculative decoding outperform fixed-length speculative decoding, and how does that change with concurrency, draft acceptance probability, and verification cost?**

## What is speculative decoding?

A small **draft model** proposes several tokens cheaply. A large **target model** **verifies** those tokens in batched form. Accepted tokens advance generation in fewer target steps; rejected tokens waste verification work.

| Policy | Behavior |
|--------|----------|
| **Standard** | One target step → one token (baseline). |
| **Fixed speculative** | Draft a fixed count (1–8), verify once, accept a prefix. |
| **Adaptive** | Pick draft length each step from estimated acceptance and cost (see limitations vs production). |

## How the simulator works

1. **Workload** — `controlled` (identical requests) or `mixed` (varied lengths/acceptance).
2. **Concurrency** — Up to `num_concurrent` requests advance one decoding step per **wave**; wall-clock advances by the max step cost in the wave.
3. **Costs** — Configurable draft cost, target AR cost, verification cost, batching efficiency, and memory-pressure past a saturation point.
4. **Acceptance** — Position-dependent probabilities: `p_i = base_acceptance × decay^i`, sampled sequentially until first rejection.
5. **Randomness** — Shared workload per experiment; each policy uses `seed + policy_offset` for acceptance sampling (documented in API meta).

### Adaptive policy (simplified)

At each step the adaptive policy scores draft lengths 1…`max_adaptive_draft_length` using:

`score = E[useful tokens] / (draft_cost + verify_cost + overhead)`

Optional **estimation noise** perturbs acceptance estimates. Optional **verification budget** skips lengths whose estimated step cost exceeds the budget.

This is **not** DeepSeek DeepInfer / DSpark: no fused KV layouts, no live logit calibration, no hardware-specific kernels.

## Project layout

```
backend/
  simulator/     # workload, acceptance, costs, engine
  policies/      # standard, fixed, adaptive stepping
  experiments/   # runner, sweeps, insights, export
  api/           # FastAPI routes + Pydantic schemas
frontend/        # React + Vite dashboard
tests/           # pytest
```

## Installation (macOS, Apple Silicon)

### Backend

```bash
cd speculative_decoding
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Run locally

**Terminal 1 — API**

```bash
cd speculative_decoding
source .venv/bin/activate
cd backend
PYTHONPATH=. uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — UI**

```bash
cd speculative_decoding/frontend
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). The Vite dev server proxies `/api` to port 8000.

## Tests

```bash
cd speculative_decoding
source .venv/bin/activate
pip install -r backend/requirements.txt
pytest tests/ -q
```

## Reproducibility

Set **Random seed** in the dashboard (or `random_seed` in API). Identical parameters reproduce identical simulation outputs.

## New experiment tools

| Feature | How to use |
|---------|------------|
| **Presets** | Click a preset card at the top (e.g. long-context cost, noisy adaptive). |
| **Multi-seed batch** | Set “Batch seeds”, click **Multi-seed batch** — bar chart with mean ± std throughput. |
| **Step replay** | Choose replay policy, click **Step replay** — table of draft/verify steps for one request. |
| **Save & compare runs** | After **Run experiment**, save with a label; pick two saved runs to diff throughput. |
| **Hypothesis check** | Enter a phrase like `adaptive beats fixed` and **Test hypothesis**. |
| **Sequence-length cost** | Set **Sequence-length cost scale** & **Prompt length** — verify/AR cost grows with context. |

Optional: `docker compose up --build` (requires Docker).

## Export

After running an experiment, use **Export JSON** or **Export CSV**, or call:

- `POST /api/export/json`
- `POST /api/export/csv`

## Sample experiment (starting point)

Use defaults except:

- `num_concurrent`: 4  
- `fixed_draft_length`: 4  
- `base_acceptance`: 0.85  
- `acceptance_decay`: 0.92  
- `random_seed`: 42  

**Hypothesis:** Fixed speculative decoding beats standard AR when acceptance is high, but adaptive reduces rejected draft tokens when decay makes long fixed drafts wasteful.

Then run **Concurrency sweep** and **Acceptance sweep** to see where each policy wins.

## Chart guide

| Chart | Meaning |
|-------|---------|
| Throughput vs concurrency | tok/s vs parallel slots (from sweep). |
| Latency vs throughput | Mean latency vs tok/s trade-off per policy. |
| Draft length vs useful tokens | Analytic expected accepted tokens vs draft length. |
| Wasted verification | Accepted vs rejected draft tokens (fixed vs adaptive). |
| Acceptance sensitivity | Throughput vs base acceptance probability. |
| Fixed vs adaptive comparison | Fixed policy at each draft length vs adaptive on same workload seed. |

## Assumptions & limitations

- Costs are **unitless** simulated values, not measured on Apple Silicon or NVIDIA hardware.
- Verification batching is a configurable curve, not a profiled kernel.
- Bonus token on full draft acceptance is modeled simplistically.
- Mixed workloads use stochastic per-request parameters; use `controlled` mode for strict comparisons.

## Future work

- Plug in traces from a real inference engine (vLLM, TensorRT-LLM, DeepInfer).
- Replace analytic adaptive scoring with live draft confidence from logits.
- Add queueing disciplines and preemption.

## License

MIT (add a LICENSE file if you publish publicly).
# speculative_decoding_exp
