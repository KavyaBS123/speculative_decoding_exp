"""Generate reproducible request workloads for simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from simulator.acceptance import acceptance_probs_for_positions


WorkloadMode = Literal["controlled", "mixed"]


@dataclass
class RequestSpec:
    request_id: int
    arrival_time: float
    prompt_length: int
    output_tokens: int
    base_acceptance: float
    acceptance_decay: float


@dataclass
class Workload:
    requests: list[RequestSpec]
    acceptance_probs_template: np.ndarray  # max draft length template for UI


class WorkloadGenerator:
    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed)

    def generate(
        self,
        num_requests: int,
        output_tokens: int,
        base_acceptance: float,
        acceptance_decay: float,
        max_draft_length: int,
        mode: WorkloadMode,
        prompt_length: int = 128,
    ) -> Workload:
        requests: list[RequestSpec] = []
        for i in range(num_requests):
            if mode == "controlled":
                out_len = output_tokens
                base_acc = base_acceptance
                decay = acceptance_decay
                plen = prompt_length
            else:
                out_len = int(self.rng.integers(max(16, output_tokens // 2), output_tokens * 2 + 1))
                base_acc = float(np.clip(base_acceptance + self.rng.normal(0, 0.08), 0.05, 0.99))
                decay = float(np.clip(acceptance_decay + self.rng.normal(0, 0.03), 0.5, 1.0))
                plen = int(self.rng.integers(32, 512))
            # Stagger arrivals slightly for mixed realism; controlled uses 0
            arrival = 0.0 if mode == "controlled" else float(self.rng.exponential(0.01))
            requests.append(
                RequestSpec(
                    request_id=i,
                    arrival_time=arrival,
                    prompt_length=plen,
                    output_tokens=out_len,
                    base_acceptance=base_acc,
                    acceptance_decay=decay,
                )
            )
        template = acceptance_probs_for_positions(base_acceptance, acceptance_decay, max_draft_length)
        return Workload(requests=requests, acceptance_probs_template=template)
