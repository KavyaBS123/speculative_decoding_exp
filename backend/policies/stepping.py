"""Shared request state and one-decoding-step implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from policies.base import SimConfig
from simulator.acceptance import expected_accepted_tokens, sample_accepted_count
from simulator.costs import draft_cost_for_length, target_autoregressive_step_cost, verify_cost
from simulator.workload import RequestSpec


PolicyKind = Literal["standard", "fixed_speculative", "adaptive"]


@dataclass
class RequestState:
    spec: RequestSpec
    remaining: int
    acceptance_probs: np.ndarray
    accumulated_cost: float = 0.0
    draft_proposed: int = 0
    draft_accepted: int = 0
    draft_rejected: int = 0
    verifications: int = 0


def _sequence_length(state: RequestState) -> int:
    generated = state.spec.output_tokens - state.remaining
    return state.spec.prompt_length + generated


@dataclass
class StepOutcome:
    execution_cost: float
    tokens_produced: int
    draft_proposed: int = 0
    draft_accepted: int = 0
    draft_rejected: int = 0
    verifications: int = 0
    done: bool = False
    bonus_tokens: int = 0
    sequence_length: int = 0
    chosen_draft_length: int = 0


def init_state(spec: RequestSpec, config: SimConfig) -> RequestState:
    from simulator.acceptance import acceptance_probs_for_positions

    probs = acceptance_probs_for_positions(
        spec.base_acceptance, spec.acceptance_decay, config.max_draft_length
    )
    return RequestState(spec=spec, remaining=spec.output_tokens, acceptance_probs=probs)


def step_standard(state: RequestState, config: SimConfig, concurrency: int, rng: np.random.Generator) -> StepOutcome:
    del rng
    if state.remaining <= 0:
        return StepOutcome(execution_cost=0.0, tokens_produced=0, done=True)
    seq = _sequence_length(state)
    cost = target_autoregressive_step_cost(
        config.target_cost_per_token,
        concurrency,
        config.verify_efficiency_at_concurrency,
        config.saturation_concurrency,
        config.memory_pressure_factor,
        seq,
        config.sequence_length_cost_scale,
    )
    state.remaining -= 1
    state.accumulated_cost += cost
    done = state.remaining <= 0
    return StepOutcome(
        execution_cost=cost, tokens_produced=1, done=done, sequence_length=seq, chosen_draft_length=0
    )


def step_fixed(
    state: RequestState, config: SimConfig, concurrency: int, rng: np.random.Generator
) -> StepOutcome:
    if state.remaining <= 0:
        return StepOutcome(execution_cost=0.0, tokens_produced=0, done=True)
    draft_len = max(1, min(config.fixed_draft_length, config.max_draft_length))
    L = min(draft_len, state.remaining)
    seq = _sequence_length(state)
    v_cost = verify_cost(
        config.verify_cost_base,
        concurrency,
        config.verify_efficiency_at_concurrency,
        config.saturation_concurrency,
        config.memory_pressure_factor,
        seq,
        config.sequence_length_cost_scale,
    )
    draft_c = draft_cost_for_length(L, config.draft_cost_per_token)
    accepted = sample_accepted_count(rng, state.acceptance_probs, L)
    bonus = 1 if accepted == L and state.remaining > L else 0
    tokens_out = min(state.remaining, accepted + bonus)
    rejected = L - min(accepted, L)
    cost = draft_c + v_cost + config.speculation_overhead
    state.remaining -= tokens_out
    state.accumulated_cost += cost
    state.draft_proposed += L
    state.draft_accepted += min(accepted, L)
    state.draft_rejected += rejected
    state.verifications += 1
    return StepOutcome(
        execution_cost=cost,
        tokens_produced=tokens_out,
        draft_proposed=L,
        draft_accepted=min(accepted, L),
        draft_rejected=rejected,
        verifications=1,
        done=state.remaining <= 0,
        bonus_tokens=bonus,
        sequence_length=seq,
        chosen_draft_length=L,
    )


def _estimate_probs(true_probs: np.ndarray, config: SimConfig, rng: np.random.Generator) -> np.ndarray:
    if config.estimation_noise <= 0:
        return true_probs.copy()
    noise = rng.normal(0, config.estimation_noise, size=true_probs.shape)
    return np.clip(true_probs + noise, 0.01, 0.99)


def _choose_adaptive_length(
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
        p_all = float(np.prod(estimated_probs[:L]))
        e_useful = e_acc + p_all if remaining > L else e_acc
        draft_c = draft_cost_for_length(L, config.draft_cost_per_token)
        total_c = draft_c + v_cost + config.speculation_overhead
        if config.verification_budget > 0 and total_c > config.verification_budget:
            continue
        score = e_useful / total_c
        if score > best_score:
            best_score = score
            best_l = L
    return best_l


def step_adaptive(
    state: RequestState, config: SimConfig, concurrency: int, rng: np.random.Generator
) -> StepOutcome:
    if state.remaining <= 0:
        return StepOutcome(execution_cost=0.0, tokens_produced=0, done=True)
    seq = _sequence_length(state)
    v_cost = verify_cost(
        config.verify_cost_base,
        concurrency,
        config.verify_efficiency_at_concurrency,
        config.saturation_concurrency,
        config.memory_pressure_factor,
        seq,
        config.sequence_length_cost_scale,
    )
    est = _estimate_probs(state.acceptance_probs, config, rng)
    L = _choose_adaptive_length(est, state.remaining, config, v_cost)
    draft_c = draft_cost_for_length(L, config.draft_cost_per_token)
    accepted = sample_accepted_count(rng, state.acceptance_probs, L)
    bonus = 1 if accepted == L and state.remaining > L else 0
    tokens_out = min(state.remaining, accepted + bonus)
    rejected = L - min(accepted, L)
    cost = draft_c + v_cost + config.speculation_overhead
    state.remaining -= tokens_out
    state.accumulated_cost += cost
    state.draft_proposed += L
    state.draft_accepted += min(accepted, L)
    state.draft_rejected += rejected
    state.verifications += 1
    return StepOutcome(
        execution_cost=cost,
        tokens_produced=tokens_out,
        draft_proposed=L,
        draft_accepted=min(accepted, L),
        draft_rejected=rejected,
        verifications=1,
        done=state.remaining <= 0,
        bonus_tokens=bonus,
        sequence_length=seq,
        chosen_draft_length=L,
    )


STEP_FN = {
    "standard": step_standard,
    "fixed_speculative": step_fixed,
    "adaptive": step_adaptive,
}
