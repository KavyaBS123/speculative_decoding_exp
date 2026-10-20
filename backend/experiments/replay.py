from __future__ import annotations

from typing import Any, Literal

import numpy as np

from experiments.runner import _config_from_params
from policies.stepping import STEP_FN, PolicyKind, init_state
from simulator.workload import WorkloadGenerator

POLICY_OFFSET = {"standard": 0, "fixed_speculative": 1000, "adaptive": 2000}


def replay_request(
    params: dict[str, Any],
    policy: PolicyKind,
    max_steps: int = 40,
) -> dict[str, Any]:
    if max_steps < 1 or max_steps > 500:
        raise ValueError("max_steps must be between 1 and 500")
    config = _config_from_params(params)
    seed = int(params["random_seed"])
    workload = WorkloadGenerator(seed).generate(
        num_requests=1,
        output_tokens=int(params["output_tokens_per_request"]),
        base_acceptance=config.base_acceptance,
        acceptance_decay=config.acceptance_decay,
        max_draft_length=config.max_draft_length,
        mode=params["workload_mode"],
        prompt_length=int(params.get("prompt_length", 128)),
    )
    spec = workload.requests[0]
    state = init_state(spec, config)
    rng = np.random.default_rng(seed + POLICY_OFFSET[policy])
    step_fn = STEP_FN[policy]
    concurrency = max(1, min(config.num_concurrent, 1))

    steps: list[dict[str, Any]] = []
    sim_time = 0.0
    step_num = 0
    while state.remaining > 0 and step_num < max_steps:
        outcome = step_fn(state, config, concurrency, rng)
        sim_time += outcome.execution_cost
        steps.append(
            {
                "step": step_num + 1,
                "sequence_length": outcome.sequence_length,
                "draft_length": outcome.chosen_draft_length,
                "draft_accepted": outcome.draft_accepted,
                "draft_rejected": outcome.draft_rejected,
                "bonus_tokens": outcome.bonus_tokens,
                "tokens_produced": outcome.tokens_produced,
                "execution_cost": outcome.execution_cost,
                "remaining_tokens": state.remaining,
                "cumulative_cost": state.accumulated_cost,
                "sim_time": sim_time,
            }
        )
        step_num += 1
        if outcome.done:
            break

    return {
        "policy": policy,
        "request": {
            "prompt_length": spec.prompt_length,
            "output_tokens": spec.output_tokens,
            "base_acceptance": spec.base_acceptance,
            "acceptance_decay": spec.acceptance_decay,
        },
        "steps": steps,
        "completed": state.remaining <= 0,
        "disclaimer": "SIMULATED RESULTS — NOT REAL GPU BENCHMARKS",
    }
