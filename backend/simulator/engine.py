"""Concurrent request simulation with C parallel decoding slots."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from policies.base import SimConfig
from policies.stepping import STEP_FN, PolicyKind, RequestState, init_state
from simulator.workload import Workload


@dataclass
class SimulationResult:
    policy: PolicyKind
    throughput_tokens_per_sec: float
    mean_latency: float
    p95_latency: float
    total_execution_cost: float
    avg_accepted_per_verification: float
    draft_tokens_rejected: int
    verification_operations: int
    speculation_efficiency: float
    total_output_tokens: int
    draft_tokens_accepted: int
    draft_tokens_proposed: int
    completion_time: float
    per_request_latencies: list[float] = field(default_factory=list)


def _simulate_policy(
    workload: Workload,
    config: SimConfig,
    policy: PolicyKind,
    seed: int,
) -> SimulationResult:
    rng = np.random.default_rng(seed)
    step_fn = STEP_FN[policy]
    specs = sorted(workload.requests, key=lambda r: r.arrival_time)
    pending = [init_state(s, config) for s in specs]
    active: list[RequestState] = []
    completion_times: dict[int, float] = {}
    sim_time = 0.0

    total_draft_prop = total_draft_acc = total_draft_rej = verifications = 0
    total_execution_cost = 0.0

    while pending or active:
        # Admit requests whose arrival time has passed
        while pending and len(active) < config.num_concurrent:
            nxt = pending.pop(0)
            if nxt.spec.arrival_time <= sim_time:
                active.append(nxt)
            else:
                pending.insert(0, nxt)
                break

        if not active:
            if pending:
                sim_time = pending[0].spec.arrival_time
                continue
            break

        concurrency = len(active)
        wave_cost = 0.0
        still_active: list[RequestState] = []
        completed_ids: list[int] = []
        for state in active:
            outcome = step_fn(state, config, concurrency, rng)
            wave_cost = max(wave_cost, outcome.execution_cost)
            total_execution_cost += outcome.execution_cost
            total_draft_prop += outcome.draft_proposed
            total_draft_acc += outcome.draft_accepted
            total_draft_rej += outcome.draft_rejected
            verifications += outcome.verifications
            if outcome.done:
                completed_ids.append(state.spec.request_id)
            else:
                still_active.append(state)

        sim_time += wave_cost
        for rid in completed_ids:
            completion_times[rid] = sim_time
        active = still_active

        # Fill slots after a wave
        while pending and len(active) < config.num_concurrent:
            nxt = pending.pop(0)
            if nxt.spec.arrival_time <= sim_time:
                active.append(nxt)
            else:
                pending.insert(0, nxt)
                break

    latencies = []
    for spec in workload.requests:
        finish = completion_times.get(spec.request_id, sim_time)
        latencies.append(finish - spec.arrival_time)

    total_tokens = sum(r.output_tokens for r in workload.requests)
    completion_time = sim_time
    throughput = total_tokens / completion_time if completion_time > 0 else 0.0
    mean_lat = float(np.mean(latencies)) if latencies else 0.0
    p95_lat = float(np.percentile(latencies, 95)) if latencies else 0.0

    return SimulationResult(
        policy=policy,
        throughput_tokens_per_sec=throughput,
        mean_latency=mean_lat,
        p95_latency=p95_lat,
        total_execution_cost=total_execution_cost,
        avg_accepted_per_verification=(total_draft_acc / verifications if verifications else 0.0),
        draft_tokens_rejected=total_draft_rej,
        verification_operations=verifications,
        speculation_efficiency=(
            total_tokens / total_execution_cost if total_execution_cost > 0 else 0.0
        ),
        total_output_tokens=total_tokens,
        draft_tokens_accepted=total_draft_acc,
        draft_tokens_proposed=total_draft_prop,
        completion_time=completion_time,
        per_request_latencies=latencies,
    )


class SimulationEngine:
    """Runs all policies on the same workload; separate RNG seeds per policy (documented)."""

    def run_all(
        self,
        workload: Workload,
        config: SimConfig,
        seed: int,
    ) -> dict[PolicyKind, SimulationResult]:
        results = {}
        for i, policy in enumerate(["standard", "fixed_speculative", "adaptive"]):
            # Shared workload; policy-specific RNG stream for acceptance sampling
            results[policy] = _simulate_policy(workload, config, policy, seed + i * 1000)
        return results
