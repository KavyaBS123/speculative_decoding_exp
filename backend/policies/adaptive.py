"""Policy C: adaptive draft length from estimated tokens per unit cost."""

from __future__ import annotations

import numpy as np

from policies.base import DecodingPolicy, PolicyMetrics, SimConfig
from simulator.acceptance import expected_accepted_tokens, sample_accepted_count
from simulator.costs import draft_cost_for_length, verify_cost
from simulator.workload import RequestSpec


class AdaptiveSpeculativePolicy(DecodingPolicy):
    """
    Simplified adaptive policy: pick draft length maximizing E[useful tokens] / cost.

    Differs from production systems (e.g. DeepSeek DeepInfer / DSpark): no KV-cache
    layout, no fused kernels, no online calibration from real logits — only this
    simulator's configurable cost and acceptance models.
    """

    name = "adaptive"

    def _estimate_probs(
        self, true_probs: np.ndarray, config: SimConfig, rng: np.random.Generator
    ) -> np.ndarray:
        if config.estimation_noise <= 0:
            return true_probs.copy()
        noise = rng.normal(0, config.estimation_noise, size=true_probs.shape)
        return np.clip(true_probs + noise, 0.01, 0.99)

    def _choose_draft_length(
        self,
        estimated_probs: np.ndarray,
        remaining: int,
        config: SimConfig,
        v_cost: float,
    ) -> int:
        max_l = min(config.max_adaptive_draft_length, config.max_draft_length, remaining)
        best_l = 1
        best_score = -1.0
        for L in range(1, max_l + 1):
            e_acc = expected_accepted_tokens(estimated_probs, L)
            # Bonus token expectation when all L accepted
            p_all = float(np.prod(estimated_probs[:L]))
            e_useful = e_acc + p_all if remaining > L else e_acc
            draft_c = draft_cost_for_length(L, config.draft_cost_per_token)
            total_c = draft_c + v_cost + config.speculation_overhead
            if total_c > config.verification_budget > 0:
                continue
            score = e_useful / total_c
            if score > best_score:
                best_score = score
                best_l = L
        return best_l

    def run_request(
        self,
        request: RequestSpec,
        config: SimConfig,
        rng: np.random.Generator,
        concurrency: int,
    ) -> tuple[PolicyMetrics, float]:
        true_probs = self.acceptance_probs(request, config)
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
            est = self._estimate_probs(true_probs, config, rng)
            L = self._choose_draft_length(est, remaining, config, v_cost)
            draft_proposed += L
            draft_c = draft_cost_for_length(L, config.draft_cost_per_token)
            accepted = sample_accepted_count(rng, true_probs, L)
            bonus = 1 if accepted == L and remaining > L else 0
            tokens_out = min(remaining, accepted + bonus)
            rejected = L - min(accepted, L)
            draft_accepted += min(accepted, L)
            draft_rejected += rejected
            verifications += 1
            cost += draft_c + v_cost + config.speculation_overhead
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
