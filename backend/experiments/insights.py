"""Rule-based interpretations from simulation outputs only."""

from __future__ import annotations

from simulator.engine import SimulationResult


def generate_insights(results: dict[str, SimulationResult]) -> list[str]:
    std = results["standard"]
    fix = results["fixed_speculative"]
    adp = results["adaptive"]
    insights: list[str] = []

    best = max(results.values(), key=lambda r: r.throughput_tokens_per_sec)
    insights.append(
        f"Highest simulated throughput ({best.throughput_tokens_per_sec:.1f} tok/s) "
        f"came from the **{best.policy.replace('_', ' ')}** policy under this configuration."
    )

    if adp.draft_tokens_rejected < fix.draft_tokens_rejected and fix.draft_tokens_proposed > 0:
        insights.append(
            "Adaptive speculation rejected fewer draft tokens than fixed-length speculation, "
            "suggesting shorter drafts when later positions are unlikely to accept."
        )
    elif fix.draft_tokens_rejected > adp.draft_tokens_rejected * 1.2:
        insights.append(
            "Fixed-length drafting proposed more tokens that were later rejected; "
            "adaptive length selection reduced wasted verification work."
        )

    if fix.throughput_tokens_per_sec > std.throughput_tokens_per_sec * 1.05:
        insights.append(
            "Fixed speculative decoding beat the autoregressive baseline on throughput — "
            "acceptance and verification costs favored drafting here."
        )
    elif fix.throughput_tokens_per_sec < std.throughput_tokens_per_sec * 0.98:
        insights.append(
            "Fixed speculative decoding did not beat the baseline; draft or verification overhead "
            "likely outweighed gains from accepting multiple tokens per step."
        )

    if adp.throughput_tokens_per_sec > fix.throughput_tokens_per_sec * 1.02:
        insights.append(
            "Adaptive draft-length selection improved throughput versus a single fixed draft length, "
            "consistent with better cost-adjusted token yield per verification."
        )
    elif adp.throughput_tokens_per_sec < fix.throughput_tokens_per_sec * 0.98:
        insights.append(
            "Adaptive policy underperformed fixed-length speculation — estimates or overhead "
            "may have favored suboptimal draft lengths in this run."
        )

    if fix.avg_accepted_per_verification < 1.2 and fix.draft_tokens_proposed > 0:
        insights.append(
            "Low average accepted tokens per verification suggests speculation may not be "
            "worthwhile unless acceptance probability or batching efficiency improves."
        )

    if std.mean_latency < fix.mean_latency and std.mean_latency < adp.mean_latency:
        insights.append(
            "Autoregressive decoding had lower mean latency in this run; higher throughput from "
            "speculation can still coexist with longer tail latency under concurrency."
        )

    return insights
