from __future__ import annotations

from typing import Any

import numpy as np

from experiments.insights import generate_insights
from policies.base import SimConfig
from simulator.acceptance import acceptance_probs_for_positions, expected_accepted_tokens
from simulator.engine import SimulationEngine, SimulationResult
from simulator.workload import WorkloadGenerator


def _config_from_params(p: dict[str, Any]) -> SimConfig:
    return SimConfig(
        num_concurrent=int(p["num_concurrent"]),
        fixed_draft_length=int(p["fixed_draft_length"]),
        max_adaptive_draft_length=int(p["max_adaptive_draft_length"]),
        base_acceptance=float(p["base_acceptance"]),
        acceptance_decay=float(p["acceptance_decay"]),
        draft_cost_per_token=float(p["draft_cost_per_token"]),
        target_cost_per_token=float(p["target_cost_per_token"]),
        verify_cost_base=float(p["verify_cost_base"]),
        verify_efficiency_at_concurrency=float(p["verify_efficiency_at_concurrency"]),
        saturation_concurrency=int(p["saturation_concurrency"]),
        memory_pressure_factor=float(p["memory_pressure_factor"]),
        verification_budget=float(p["verification_budget"]),
        estimation_noise=float(p["estimation_noise"]),
        speculation_overhead=float(p.get("speculation_overhead", 0.02)),
        max_draft_length=int(p.get("max_draft_length", 8)),
        sequence_length_cost_scale=float(p.get("sequence_length_cost_scale", 0.0)),
    )


def _result_dict(r: SimulationResult) -> dict[str, Any]:
    return {
        "policy": r.policy,
        "throughput_tokens_per_sec": r.throughput_tokens_per_sec,
        "mean_latency": r.mean_latency,
        "p95_latency": r.p95_latency,
        "total_execution_cost": r.total_execution_cost,
        "avg_accepted_per_verification": r.avg_accepted_per_verification,
        "draft_tokens_rejected": r.draft_tokens_rejected,
        "verification_operations": r.verification_operations,
        "speculation_efficiency": r.speculation_efficiency,
        "total_output_tokens": r.total_output_tokens,
        "draft_tokens_accepted": r.draft_tokens_accepted,
        "draft_tokens_proposed": r.draft_tokens_proposed,
        "completion_time": r.completion_time,
    }


class ExperimentRunner:
    def __init__(self) -> None:
        self.engine = SimulationEngine()

    def run_experiment(self, params: dict[str, Any]) -> dict[str, Any]:
        config = _config_from_params(params)
        seed = int(params["random_seed"])
        num_requests = int(params["num_requests"])
        output_tokens = int(params["output_tokens_per_request"])
        mode = params["workload_mode"]
        prompt_length = int(params.get("prompt_length", 128))

        workload = WorkloadGenerator(seed).generate(
            num_requests=num_requests,
            output_tokens=output_tokens,
            base_acceptance=config.base_acceptance,
            acceptance_decay=config.acceptance_decay,
            max_draft_length=config.max_draft_length,
            mode=mode,
            prompt_length=prompt_length,
        )
        results = self.engine.run_all(workload, config, seed)
        insights = generate_insights(results)

        chart_draft_length = self._draft_length_curve(config)
        chart_wasted = {
            "fixed": {
                "accepted": results["fixed_speculative"].draft_tokens_accepted,
                "rejected": results["fixed_speculative"].draft_tokens_rejected,
            },
            "adaptive": {
                "accepted": results["adaptive"].draft_tokens_accepted,
                "rejected": results["adaptive"].draft_tokens_rejected,
            },
        }

        return {
            "results": {k: _result_dict(v) for k, v in results.items()},
            "insights": insights,
            "charts": {
                "draft_length_vs_useful": chart_draft_length,
                "wasted_verification": chart_wasted,
            },
            "meta": {
                "random_seed": seed,
                "workload_mode": mode,
                "num_requests": num_requests,
                "disclaimer": "SIMULATED RESULTS — NOT REAL GPU BENCHMARKS",
            },
        }

    def _draft_length_curve(self, config: SimConfig) -> list[dict[str, float]]:
        probs = acceptance_probs_for_positions(
            config.base_acceptance, config.acceptance_decay, config.max_draft_length
        )
        curve = []
        for L in range(1, config.max_draft_length + 1):
            e_acc = expected_accepted_tokens(probs, L)
            p_all = float(np.prod(probs[:L]))
            curve.append(
                {
                    "draft_length": L,
                    "expected_accepted": e_acc,
                    "expected_with_bonus": e_acc + p_all,
                }
            )
        return curve

    def sweep_concurrency(self, params: dict[str, Any], values: list[int]) -> dict[str, Any]:
        series: list[dict[str, Any]] = []
        for c in values:
            p = {**params, "num_concurrent": c}
            run = self.run_experiment(p)
            for policy, res in run["results"].items():
                series.append(
                    {
                        "concurrency": c,
                        "policy": policy,
                        "throughput_tokens_per_sec": res["throughput_tokens_per_sec"],
                        "mean_latency": res["mean_latency"],
                        "p95_latency": res["p95_latency"],
                    }
                )
        return {"series": series, "disclaimer": "SIMULATED RESULTS — NOT REAL GPU BENCHMARKS"}

    def sweep_acceptance(self, params: dict[str, Any], values: list[float]) -> dict[str, Any]:
        series: list[dict[str, Any]] = []
        for a in values:
            p = {**params, "base_acceptance": a}
            run = self.run_experiment(p)
            for policy, res in run["results"].items():
                series.append(
                    {
                        "base_acceptance": a,
                        "policy": policy,
                        "throughput_tokens_per_sec": res["throughput_tokens_per_sec"],
                    }
                )
        return {"series": series, "disclaimer": "SIMULATED RESULTS — NOT REAL GPU BENCHMARKS"}

    def compare_fixed_lengths(self, params: dict[str, Any]) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        base = _config_from_params(params)
        for L in range(1, base.max_draft_length + 1):
            p = {**params, "fixed_draft_length": L}
            run = self.run_experiment(p)
            fix = run["results"]["fixed_speculative"]
            adp = run["results"]["adaptive"]
            rows.append(
                {
                    "fixed_draft_length": L,
                    "fixed_throughput": fix["throughput_tokens_per_sec"],
                    "adaptive_throughput": adp["throughput_tokens_per_sec"],
                    "fixed_rejected": fix["draft_tokens_rejected"],
                    "adaptive_rejected": adp["draft_tokens_rejected"],
                }
            )
        return {"comparison": rows, "disclaimer": "SIMULATED RESULTS — NOT REAL GPU BENCHMARKS"}

    def export_flat_rows(self, experiment: dict[str, Any]) -> list[dict[str, Any]]:
        rows = []
        for policy, res in experiment["results"].items():
            row = {"policy": policy, **res}
            rows.append(row)
        return rows
