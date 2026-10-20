"""Built-in experiment presets (parameter overrides only)."""

from __future__ import annotations

from typing import Any

PRESETS: dict[str, dict[str, Any]] = {
    "baseline_friendly": {
        "name": "High acceptance (speculation-friendly)",
        "description": "Strong draft acceptance, moderate draft cost — speculation often wins.",
        "overrides": {
            "base_acceptance": 0.92,
            "acceptance_decay": 0.96,
            "fixed_draft_length": 4,
            "draft_cost_per_token": 0.12,
            "num_concurrent": 4,
        },
    },
    "low_acceptance_stress": {
        "name": "Low acceptance stress test",
        "description": "Drafts often fail; tests when AR baseline beats speculation.",
        "overrides": {
            "base_acceptance": 0.45,
            "acceptance_decay": 0.88,
            "fixed_draft_length": 6,
            "draft_cost_per_token": 0.2,
        },
    },
    "long_context_cost": {
        "name": "Long-context verify cost",
        "description": "Verification cost grows with sequence length (KV-style model).",
        "overrides": {
            "prompt_length": 2048,
            "output_tokens_per_request": 256,
            "sequence_length_cost_scale": 0.35,
            "base_acceptance": 0.82,
        },
    },
    "noisy_adaptive": {
        "name": "Noisy adaptive estimates",
        "description": "Adaptive policy with imperfect acceptance estimation.",
        "overrides": {
            "estimation_noise": 0.12,
            "max_adaptive_draft_length": 6,
            "verification_budget": 2.5,
        },
    },
    "mixed_workload": {
        "name": "Mixed workload",
        "description": "Varied output lengths and per-request acceptance.",
        "overrides": {
            "workload_mode": "mixed",
            "num_requests": 16,
            "num_concurrent": 8,
        },
    },
}


def list_presets() -> list[dict[str, Any]]:
    return [
        {"id": pid, "name": p["name"], "description": p["description"], "overrides": p["overrides"]}
        for pid, p in PRESETS.items()
    ]


def apply_preset(preset_id: str, base_params: dict[str, Any]) -> dict[str, Any]:
    if preset_id not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_id}")
    merged = {**base_params, **PRESETS[preset_id]["overrides"]}
    return merged
