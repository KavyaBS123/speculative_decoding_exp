from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ExperimentParams(BaseModel):
    num_requests: int = Field(8, ge=1, le=256)
    num_concurrent: int = Field(4, ge=1, le=64)
    fixed_draft_length: int = Field(4, ge=1, le=8)
    max_adaptive_draft_length: int = Field(8, ge=1, le=8)
    max_draft_length: int = Field(8, ge=1, le=8)
    base_acceptance: float = Field(0.85, ge=0.01, le=0.99)
    acceptance_decay: float = Field(0.92, ge=0.5, le=1.0)
    draft_cost_per_token: float = Field(0.15, gt=0)
    target_cost_per_token: float = Field(1.0, gt=0)
    verify_cost_base: float = Field(0.9, gt=0)
    verify_efficiency_at_concurrency: float = Field(0.75, gt=0, le=1.5)
    saturation_concurrency: int = Field(8, ge=1, le=64)
    memory_pressure_factor: float = Field(0.25, ge=0)
    output_tokens_per_request: int = Field(128, ge=8, le=4096)
    prompt_length: int = Field(128, ge=8, le=8192)
    verification_budget: float = Field(0.0, ge=0, description="0 = unlimited per-step cost")
    estimation_noise: float = Field(0.0, ge=0, le=0.5)
    speculation_overhead: float = Field(0.02, ge=0)
    random_seed: int = Field(42, ge=0)
    workload_mode: Literal["controlled", "mixed"] = "controlled"
    sequence_length_cost_scale: float = Field(
        0.0,
        ge=0,
        le=2.0,
        description="Extra verify/AR cost per 1k tokens of prompt+generated (0=off)",
    )


class BatchRunRequest(BaseModel):
    params: ExperimentParams
    num_seeds: int = Field(5, ge=1, le=50)
    seed_step: int = Field(1, ge=1, le=1000)


class ReplayRequest(BaseModel):
    params: ExperimentParams
    policy: Literal["standard", "fixed_speculative", "adaptive"] = "adaptive"
    max_steps: int = Field(30, ge=1, le=500)


class HypothesisRequest(BaseModel):
    params: ExperimentParams
    hypothesis: str = Field(..., min_length=3, max_length=500)


class ApplyPresetRequest(BaseModel):
    preset_id: str
    base_params: Optional[ExperimentParams] = None


class SweepConcurrencyRequest(BaseModel):
    params: ExperimentParams
    values: list[int] = Field(default_factory=lambda: [1, 2, 4, 8, 16])


class SweepAcceptanceRequest(BaseModel):
    params: ExperimentParams
    values: list[float] = Field(default_factory=lambda: [0.5, 0.65, 0.75, 0.85, 0.95])
