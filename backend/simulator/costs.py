"""Configurable cost models — illustrative curves, not hardware measurements."""

from __future__ import annotations

import math


def verification_efficiency_multiplier(
    concurrency: int,
    base_efficiency: float,
    saturation_concurrency: int,
    memory_pressure_factor: float,
) -> float:
    """
    Multiplier applied to target verification cost per operation.

    At low concurrency, verification amortizes less (higher effective cost).
    At moderate concurrency, batching improves efficiency up to `base_efficiency`.
    Beyond `saturation_concurrency`, memory/scheduling pressure increases cost.
    """
    c = max(1, concurrency)
    # Logistic ramp toward base_efficiency (values < 1 mean cheaper per verify at higher batch)
    ramp = 1.0 - (1.0 - base_efficiency) * (1.0 - math.exp(-c / max(1, saturation_concurrency)))
    if c > saturation_concurrency:
        excess = c - saturation_concurrency
        ramp *= 1.0 + memory_pressure_factor * (excess / saturation_concurrency)
    return max(0.05, ramp)


def draft_cost_for_length(draft_length: int, draft_cost_per_token: float) -> float:
    return draft_length * draft_cost_per_token


def sequence_length_multiplier(sequence_length: int, scale_per_1k_tokens: float) -> float:
    """KV-style growth: cost increases with prompt + generated tokens (configurable, not measured)."""
    if scale_per_1k_tokens <= 0:
        return 1.0
    return 1.0 + scale_per_1k_tokens * (max(0, sequence_length) / 1000.0)


def verify_cost(
    verify_cost_base: float,
    concurrency: int,
    base_efficiency: float,
    saturation_concurrency: int,
    memory_pressure_factor: float,
    sequence_length: int = 0,
    sequence_length_cost_scale: float = 0.0,
) -> float:
    mult = verification_efficiency_multiplier(
        concurrency, base_efficiency, saturation_concurrency, memory_pressure_factor
    )
    seq_mult = sequence_length_multiplier(sequence_length, sequence_length_cost_scale)
    return verify_cost_base * mult * seq_mult


def target_autoregressive_step_cost(
    target_cost_per_token: float,
    concurrency: int,
    base_efficiency: float,
    saturation_concurrency: int,
    memory_pressure_factor: float,
    sequence_length: int = 0,
    sequence_length_cost_scale: float = 0.0,
) -> float:
    """Standard decoding: one target forward pass per token."""
    return verify_cost(
        target_cost_per_token,
        concurrency,
        base_efficiency,
        saturation_concurrency,
        memory_pressure_factor,
        sequence_length,
        sequence_length_cost_scale,
    )
