import numpy as np

from simulator.acceptance import (
    acceptance_probs_for_positions,
    expected_accepted_tokens,
    sample_accepted_count,
)


def test_acceptance_probs_decay():
    probs = acceptance_probs_for_positions(0.9, 0.9, 5)
    assert probs[0] == 0.9
    assert probs[1] < probs[0]
    assert len(probs) == 5


def test_expected_accepted_tokens():
    probs = acceptance_probs_for_positions(1.0, 1.0, 3)
    assert expected_accepted_tokens(probs, 3) == 3.0
    probs = acceptance_probs_for_positions(0.5, 1.0, 2)
    assert abs(expected_accepted_tokens(probs, 2) - 0.75) < 1e-9


def test_sample_accepted_count_bounds():
    rng = np.random.default_rng(0)
    probs = acceptance_probs_for_positions(0.8, 0.95, 4)
    for _ in range(100):
        n = sample_accepted_count(rng, probs, 4)
        assert 0 <= n <= 4
