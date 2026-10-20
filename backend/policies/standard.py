"""Policy A: one target-model step per output token."""

from __future__ import annotations

import numpy as np

from policies.base import DecodingPolicy, PolicyMetrics, SimConfig
from simulator.costs import target_autoregressive_step_cost
from simulator.workload import RequestSpec


class StandardPolicy(DecodingPolicy):
    name = "standard"

    def run_request(
        self,
        request: RequestSpec,
        config: SimConfig,
        rng: np.random.Generator,
        concurrency: int,
    ) -> tuple[PolicyMetrics, float]:
        del rng
        remaining = request.output_tokens
        cost = 0.0
        step_cost = target_autoregressive_step_cost(
            config.target_cost_per_token,
            concurrency,
            config.verify_efficiency_at_concurrency,
            config.saturation_concurrency,
            config.memory_pressure_factor,
        )
        while remaining > 0:
            cost += step_cost
            remaining -= 1
        metrics = PolicyMetrics(
            total_output_tokens=request.output_tokens,
            total_execution_cost=cost,
            request_latencies=[cost + request.arrival_time],
        )
        return metrics, cost
