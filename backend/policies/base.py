from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np

from simulator.workload import RequestSpec


@dataclass
class PolicyStepResult:
    tokens_produced: int
    execution_cost: float
    draft_tokens_proposed: int = 0
    draft_tokens_accepted: int = 0
    draft_tokens_rejected: int = 0
    verifications: int = 0


@dataclass
class PolicyMetrics:
    total_output_tokens: int = 0
    total_execution_cost: float = 0.0
    request_latencies: list[float] = field(default_factory=list)
    draft_proposed: int = 0
    draft_accepted: int = 0
    draft_rejected: int = 0
    verifications: int = 0


@dataclass
class SimConfig:
    num_concurrent: int
    fixed_draft_length: int
    max_adaptive_draft_length: int
    base_acceptance: float
    acceptance_decay: float
    draft_cost_per_token: float
    target_cost_per_token: float
    verify_cost_base: float
    verify_efficiency_at_concurrency: float
    saturation_concurrency: int
    memory_pressure_factor: float
    verification_budget: float
    estimation_noise: float
    speculation_overhead: float
    max_draft_length: int = 8
    sequence_length_cost_scale: float = 0.0


class DecodingPolicy(ABC):
    name: str

    @abstractmethod
    def run_request(
        self,
        request: RequestSpec,
        config: SimConfig,
        rng: np.random.Generator,
        concurrency: int,
    ) -> tuple[PolicyMetrics, float]:
        """Returns per-request metrics fragment and simulated time to complete."""

    def acceptance_probs(self, request: RequestSpec, config: SimConfig) -> np.ndarray:
        from simulator.acceptance import acceptance_probs_for_positions

        return acceptance_probs_for_positions(
            request.base_acceptance, request.acceptance_decay, config.max_draft_length
        )
