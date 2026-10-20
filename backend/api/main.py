from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    ApplyPresetRequest,
    BatchRunRequest,
    ExperimentParams,
    HypothesisRequest,
    ReplayRequest,
    SweepAcceptanceRequest,
    SweepConcurrencyRequest,
)
from experiments.batch import run_batch
from experiments.export import results_to_csv, results_to_json
from experiments.hypothesis import evaluate_hypothesis
from experiments.presets import apply_preset, list_presets
from experiments.replay import replay_request
from experiments.runner import ExperimentRunner

app = FastAPI(title="Speculation Budget Lab API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

runner = ExperimentRunner()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/defaults")
def defaults() -> ExperimentParams:
    return ExperimentParams()


@app.post("/api/experiment/run")
def run_experiment(params: ExperimentParams) -> dict:
    try:
        return runner.run_experiment(params.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/experiment/sweep/concurrency")
def sweep_concurrency(body: SweepConcurrencyRequest) -> dict:
    if not body.values:
        raise HTTPException(status_code=400, detail="values must not be empty")
    return runner.sweep_concurrency(body.params.model_dump(), body.values)


@app.post("/api/experiment/sweep/acceptance")
def sweep_acceptance(body: SweepAcceptanceRequest) -> dict:
    if not body.values:
        raise HTTPException(status_code=400, detail="values must not be empty")
    return runner.sweep_acceptance(body.params.model_dump(), body.values)


@app.post("/api/experiment/compare/fixed-lengths")
def compare_fixed(params: ExperimentParams) -> dict:
    return runner.compare_fixed_lengths(params.model_dump())


@app.post("/api/export/json")
def export_json(params: ExperimentParams) -> dict:
    data = runner.run_experiment(params.model_dump())
    return {"content": results_to_json(data)}


@app.post("/api/export/csv")
def export_csv(params: ExperimentParams) -> dict:
    data = runner.run_experiment(params.model_dump())
    rows = runner.export_flat_rows(data)
    return {"content": results_to_csv(rows)}


@app.get("/api/presets")
def get_presets() -> dict:
    return {"presets": list_presets()}


@app.post("/api/presets/apply")
def post_apply_preset(body: ApplyPresetRequest) -> ExperimentParams:
    base = (body.base_params or ExperimentParams()).model_dump()
    try:
        merged = apply_preset(body.preset_id, base)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ExperimentParams(**merged)


@app.post("/api/experiment/batch")
def experiment_batch(body: BatchRunRequest) -> dict:
    try:
        return run_batch(body.params.model_dump(), body.num_seeds, body.seed_step)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/experiment/replay")
def experiment_replay(body: ReplayRequest) -> dict:
    try:
        return replay_request(body.params.model_dump(), body.policy, body.max_steps)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/experiment/hypothesis")
def experiment_hypothesis(body: HypothesisRequest) -> dict:
    run = runner.run_experiment(body.params.model_dump())
    evaluation = evaluate_hypothesis(body.hypothesis, run)
    return {"experiment": run, "evaluation": evaluation}
