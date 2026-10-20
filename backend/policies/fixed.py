"""Policy B: fixed-length speculative decoding."""

from __future__ import annotations

import numpy as np

from policies.base import DecodingPolicy, PolicyMetrics, SimConfig
from simulator.acceptance import sample_accepted_count
from simulator.costs import draft_cost_for_length, verify_cost
from simulator.workload import RequestSpec


class FixedSpeculativePolicy(DecodingPolicy):
    name = "fixed_speculative"

    def run_request(
        self,
        request: RequestSpec,
        config: SimConfig,
        rng: np.random.Generator,
        concurrency: int,
    ) -> tuple[PolicyMetrics, float]:
        probs = self.acceptance_probs(request, config)
        draft_len = max(1, min(config.fixed_draft_length, config.max_draft_length))
        remaining = request.output_tokens
        cost = 0.0
        draft_proposed = draft_accepted = draft_rejected = verifications = 0

        v_cost = verify_cost(
            config.verify_cost_base,
            concurrency,
            config.verify_efficiency_at_concurrency,
            config.saturation_concurrency,
            config.memory_pressure_factor,
        )

        while remaining > 0:
            L = min(draft_len, remaining)
            draft_proposed += L
            draft_c = draft_cost_for_length(L, config.draft_cost_per_token)
            accepted = sample_accepted_count(rng, probs, L)
            # Standard speculative decoding: on full accept, target may emit one bonus token
            bonus = 1 if accepted == L and remaining > L else 0
            tokens_out = min(remaining, accepted + bonus)
            rejected = L - min(accepted, L)
            draft_accepted += min(accepted, L)
            draft_rejected += rejected
            verifications += 1

            step_cost = draft_c + v_cost + config.speculation_overhead
            cost += step_cost
            remaining -= tokens_out

        metrics = PolicyMetrics(
            total_output_tokens=request.output_tokens,
            total_execution_cost=cost,
            request_latencies=[cost + request.arrival_time],
            draft_proposed=draft_proposed,
            draft_accepted=draft_accepted,
            draft_rejected=draft_rejected,
            verifications=verifications,
        )
        return metrics, cost
