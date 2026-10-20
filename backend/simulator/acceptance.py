"""Position-dependent draft token acceptance probabilities."""

from __future__ import annotations

import numpy as np


def acceptance_probs_for_positions(
    base_acceptance: float,
    decay_per_position: float,
    max_draft_length: int,
) -> np.ndarray:
    """
    Probability that draft token at position i (0-indexed) is accepted,
    given all prior tokens were accepted.
    """
    positions = np.arange(max_draft_length, dtype=np.float64)
    probs = base_acceptance * np.power(decay_per_position, positions)
    return np.clip(probs, 0.0, 1.0)


def expected_accepted_tokens(acceptance_probs: np.ndarray, draft_length: int) -> float:
    """
    Expected number of accepted tokens when drafting `draft_length` tokens.
    E = sum_{i=0}^{L-1} prod_{j=0}^{i} p_j
    """
    if draft_length <= 0:
        return 0.0
    probs = acceptance_probs[:draft_length]
    cumulative = 1.0
    expected = 0.0
    for p in probs:
        cumulative *= p
        expected += cumulative
    return expected


def sample_accepted_count(rng: np.random.Generator, acceptance_probs: np.ndarray, draft_length: int) -> int:
    """Sample how many consecutive draft tokens are accepted (including bonus target token modeled separately)."""
    accepted = 0
    for i in range(draft_length):
        if rng.random() < acceptance_probs[i]:
            accepted += 1
        else:
            break
    return accepted
