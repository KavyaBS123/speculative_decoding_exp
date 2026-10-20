from experiments.batch import run_batch
from experiments.hypothesis import evaluate_hypothesis
from experiments.presets import apply_preset, list_presets
from experiments.replay import replay_request
from experiments.runner import ExperimentRunner
from simulator.costs import sequence_length_multiplier, verify_cost


def _params(**kw):
    p = {
        "num_requests": 2,
        "num_concurrent": 2,
        "fixed_draft_length": 3,
        "max_adaptive_draft_length": 6,
        "max_draft_length": 8,
        "base_acceptance": 0.8,
        "acceptance_decay": 0.92,
        "draft_cost_per_token": 0.15,
        "target_cost_per_token": 1.0,
        "verify_cost_base": 0.9,
        "verify_efficiency_at_concurrency": 0.75,
        "saturation_concurrency": 8,
        "memory_pressure_factor": 0.25,
        "output_tokens_per_request": 48,
        "prompt_length": 512,
        "verification_budget": 0.0,
        "estimation_noise": 0.0,
        "speculation_overhead": 0.02,
        "random_seed": 7,
        "workload_mode": "controlled",
        "sequence_length_cost_scale": 0.0,
    }
    p.update(kw)
    return p


def test_sequence_length_increases_verify_cost():
    low = verify_cost(1.0, 4, 0.8, 8, 0.2, sequence_length=100, sequence_length_cost_scale=0.5)
    high = verify_cost(1.0, 4, 0.8, 8, 0.2, sequence_length=2100, sequence_length_cost_scale=0.5)
    assert high > low
    assert sequence_length_multiplier(0, 0.5) == 1.0


def test_batch_run_aggregates():
    out = run_batch(_params(), num_seeds=3, seed_step=1)
    assert out["num_seeds"] == 3
    assert "standard" in out["aggregates"]
    assert "mean" in out["aggregates"]["adaptive"]["throughput_tokens_per_sec"]


def test_replay_produces_steps():
    out = replay_request(_params(output_tokens_per_request=24), "fixed_speculative", max_steps=20)
    assert len(out["steps"]) >= 1
    assert out["steps"][0]["draft_length"] >= 1


def test_presets_apply():
    assert len(list_presets()) >= 3
    merged = apply_preset("mixed_workload", _params())
    assert merged["workload_mode"] == "mixed"


def test_hypothesis_evaluation():
    run = ExperimentRunner().run_experiment(_params())
    ev = evaluate_hypothesis("adaptive rejects less waste", run)
    assert ev["supported"] is not None
