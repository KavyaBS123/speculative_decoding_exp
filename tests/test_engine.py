from experiments.export import results_to_csv, results_to_json
from experiments.runner import ExperimentRunner
from simulator.engine import SimulationEngine
from simulator.workload import WorkloadGenerator


def _params(**overrides):
    p = {
        "num_requests": 4,
        "num_concurrent": 2,
        "fixed_draft_length": 4,
        "max_adaptive_draft_length": 8,
        "max_draft_length": 8,
        "base_acceptance": 0.85,
        "acceptance_decay": 0.92,
        "draft_cost_per_token": 0.15,
        "target_cost_per_token": 1.0,
        "verify_cost_base": 0.9,
        "verify_efficiency_at_concurrency": 0.75,
        "saturation_concurrency": 8,
        "memory_pressure_factor": 0.25,
        "output_tokens_per_request": 64,
        "prompt_length": 128,
        "verification_budget": 0.0,
        "estimation_noise": 0.0,
        "speculation_overhead": 0.02,
        "random_seed": 123,
        "workload_mode": "controlled",
        "sequence_length_cost_scale": 0.0,
    }
    p.update(overrides)
    return p


def test_reproducibility_same_seed():
    r = ExperimentRunner()
    a = r.run_experiment(_params())
    b = r.run_experiment(_params())
    assert a["results"] == b["results"]


def test_low_acceptance_speculation_often_loses():
    r = ExperimentRunner()
    low = r.run_experiment(_params(base_acceptance=0.15, acceptance_decay=0.9))
    std_tp = low["results"]["standard"]["throughput_tokens_per_sec"]
    fix_tp = low["results"]["fixed_speculative"]["throughput_tokens_per_sec"]
    assert fix_tp <= std_tp * 1.05


def test_export_formats():
    r = ExperimentRunner()
    data = r.run_experiment(_params())
    assert "results" in results_to_json(data)
    rows = r.export_flat_rows(data)
    csv_text = results_to_csv(rows)
    assert "standard" in csv_text
    assert "throughput_tokens_per_sec" in csv_text


def test_engine_runs_all_policies():
    wg = WorkloadGenerator(7)
    wl = wg.generate(2, 32, 0.8, 0.95, 8, "controlled")
    from policies.base import SimConfig

    cfg = SimConfig(
        num_concurrent=2,
        fixed_draft_length=3,
        max_adaptive_draft_length=6,
        base_acceptance=0.8,
        acceptance_decay=0.95,
        draft_cost_per_token=0.1,
        target_cost_per_token=1.0,
        verify_cost_base=0.8,
        verify_efficiency_at_concurrency=0.8,
        saturation_concurrency=8,
        memory_pressure_factor=0.2,
        verification_budget=0.0,
        estimation_noise=0.0,
        speculation_overhead=0.01,
        max_draft_length=8,
    )
    res = SimulationEngine().run_all(wl, cfg, 99)
    assert set(res.keys()) == {"standard", "fixed_speculative", "adaptive"}
