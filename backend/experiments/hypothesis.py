"""Check simple user hypotheses against batch or single-run aggregates."""

from __future__ import annotations

from typing import Any


def evaluate_hypothesis(hypothesis: str, experiment: dict[str, Any]) -> dict[str, Any]:
    h = hypothesis.strip().lower()
    results = experiment.get("results") or {}
    if not results:
        return {"supported": None, "message": "No results to evaluate."}

    std = results.get("standard", {})
    fix = results.get("fixed_speculative", {})
    adp = results.get("adaptive", {})

    checks: list[tuple[str, bool, str]] = []

    if "adaptive" in h and ("better" in h or "beat" in h or "outperform" in h):
        if "fixed" in h:
            ok = adp.get("throughput_tokens_per_sec", 0) > fix.get("throughput_tokens_per_sec", 0)
            checks.append(
                (
                    "adaptive_vs_fixed_throughput",
                    ok,
                    f"Adaptive throughput {adp.get('throughput_tokens_per_sec', 0):.2f} vs "
                    f"fixed {fix.get('throughput_tokens_per_sec', 0):.2f} tok/s.",
                )
            )
        if "standard" in h or "baseline" in h or "autoregressive" in h:
            ok = adp.get("throughput_tokens_per_sec", 0) > std.get("throughput_tokens_per_sec", 0)
            checks.append(
                (
                    "adaptive_vs_standard",
                    ok,
                    f"Adaptive {adp.get('throughput_tokens_per_sec', 0):.2f} vs "
                    f"standard {std.get('throughput_tokens_per_sec', 0):.2f} tok/s.",
                )
            )

    if "reject" in h or "waste" in h:
        ok = adp.get("draft_tokens_rejected", 0) < fix.get("draft_tokens_rejected", 0)
        checks.append(
            (
                "adaptive_less_rejected",
                ok,
                f"Adaptive rejected {adp.get('draft_tokens_rejected', 0)} vs "
                f"fixed {fix.get('draft_tokens_rejected', 0)} draft tokens.",
            )
        )

    if "speculation" in h and ("not" in h or "fail" in h or "lose" in h):
        ok = fix.get("throughput_tokens_per_sec", 0) < std.get("throughput_tokens_per_sec", 0)
        checks.append(
            (
                "fixed_loses_to_standard",
                ok,
                f"Fixed speculative {fix.get('throughput_tokens_per_sec', 0):.2f} vs "
                f"standard {std.get('throughput_tokens_per_sec', 0):.2f} tok/s.",
            )
        )

    if not checks:
        return {
            "supported": None,
            "message": "Could not parse hypothesis. Try phrases like "
            "'adaptive beats fixed' or 'adaptive rejects less waste'.",
            "checks": [],
        }

    supported = all(c[1] for c in checks)
    messages = [c[2] for c in checks]
    return {
        "supported": supported,
        "message": "Hypothesis supported by this run." if supported else "Hypothesis not supported by this run.",
        "checks": [{"id": c[0], "passed": c[1], "detail": c[2]} for c in checks],
        "details": messages,
    }
