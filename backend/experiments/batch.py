from __future__ import annotations

from typing import Any

import numpy as np

from experiments.runner import ExperimentRunner

METRIC_KEYS = (
    "throughput_tokens_per_sec",
    "mean_latency",
    "p95_latency",
    "draft_tokens_rejected",
    "avg_accepted_per_verification",
)


def run_batch(params: dict[str, Any], num_seeds: int, seed_step: int = 1) -> dict[str, Any]:
    if num_seeds < 1 or num_seeds > 50:
        raise ValueError("num_seeds must be between 1 and 50")
    base_seed = int(params["random_seed"])
    runner = ExperimentRunner()
    by_policy: dict[str, list[dict[str, float]]] = {}
    seeds_used: list[int] = []

    for i in range(num_seeds):
        seed = base_seed + i * seed_step
        seeds_used.append(seed)
        run = runner.run_experiment({**params, "random_seed": seed})
        for policy, res in run["results"].items():
            by_policy.setdefault(policy, []).append(res)

    aggregates: dict[str, dict[str, dict[str, float]]] = {}
    for policy, rows in by_policy.items():
        aggregates[policy] = {}
        for key in METRIC_KEYS:
            vals = np.array([r[key] for r in rows], dtype=np.float64)
            aggregates[policy][key] = {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals, ddof=0)),
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
            }

    return {
        "seeds": seeds_used,
        "num_seeds": num_seeds,
        "aggregates": aggregates,
        "disclaimer": "SIMULATED RESULTS — NOT REAL GPU BENCHMARKS",
    }
