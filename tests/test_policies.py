import numpy as np

from policies.base import SimConfig
from policies.stepping import STEP_FN, init_state
from simulator.workload import RequestSpec


def _config(**kwargs) -> SimConfig:
    base = dict(
        num_concurrent=4,
        fixed_draft_length=4,
        max_adaptive_draft_length=8,
        base_acceptance=0.85,
        acceptance_decay=0.92,
        draft_cost_per_token=0.15,
        target_cost_per_token=1.0,
        verify_cost_base=0.9,
        verify_efficiency_at_concurrency=0.75,
        saturation_concurrency=8,
        memory_pressure_factor=0.25,
        verification_budget=0.0,
        estimation_noise=0.0,
        speculation_overhead=0.02,
        max_draft_length=8,
    )
    base.update(kwargs)
    return SimConfig(**base)


def _req() -> RequestSpec:
    return RequestSpec(0, 0.0, 128, 32, 0.85, 0.92)


def test_standard_one_token_per_step():
    state = init_state(_req(), _config())
    rng = np.random.default_rng(1)
    tokens = 0
    steps = 0
    while state.remaining > 0:
        out = STEP_FN["standard"](state, _config(), 1, rng)
        tokens += out.tokens_produced
        steps += 1
    assert tokens == 32
    assert steps == 32


def test_high_draft_cost_hurts_speculation():
    cfg_cheap = _config(draft_cost_per_token=0.05, base_acceptance=0.95)
    cfg_expensive = _config(draft_cost_per_token=5.0, base_acceptance=0.95)
    rng = np.random.default_rng(2)

    def total_cost(policy, cfg):
        state = init_state(_req(), cfg)
        cost = 0.0
        while state.remaining > 0:
            o = STEP_FN[policy](state, cfg, 1, rng)
            cost += o.execution_cost
        return cost

    assert total_cost("fixed_speculative", cfg_expensive) > total_cost("standard", cfg_expensive)


def test_adaptive_respects_max_length():
    cfg = _config(max_adaptive_draft_length=2, estimation_noise=0.0)
    state = init_state(_req(), cfg)
    rng = np.random.default_rng(3)
    out = STEP_FN["adaptive"](state, cfg, 4, rng)
    assert out.draft_proposed <= 2
