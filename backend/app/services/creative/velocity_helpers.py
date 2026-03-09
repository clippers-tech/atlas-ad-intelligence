"""Velocity scoring helper functions for creative analysis."""


def trend_score(values: list[float], weight: float) -> float:
    """Map linear trend of a metric series to a 0–weight score.

    Args:
        values: Time-ordered list of metric values (oldest first).
        weight: Maximum score contribution for this component.

    Returns:
        Score in [0, weight]. Neutral (weight/2) when insufficient data.
    """
    if len(values) < 2 or max(values) == 0:
        return weight / 2
    first, last = values[0], values[-1]
    if first == 0:
        return weight
    change = (last - first) / first  # e.g. +0.5 = +50%
    # Clamp to [-1, +1] then map to [0, weight]
    clamped = max(-1.0, min(1.0, change))
    return ((clamped + 1) / 2) * weight


def efficiency_score(cpl: float, target_cpl: float | None, weight: float) -> float:
    """Score CPL efficiency against an account target.

    - cpl <= target → full marks
    - cpl >= 3x target → zero
    - between → linear interpolation

    Args:
        cpl: Latest cost-per-lead for the ad.
        target_cpl: Account's target CPL; if None/zero, returns neutral score.
        weight: Maximum score contribution for this component.

    Returns:
        Score in [0, weight].
    """
    if not target_cpl or target_cpl <= 0 or cpl <= 0:
        return weight / 2
    ratio = cpl / target_cpl  # 1.0 = on target, 3.0 = 3x target
    if ratio <= 1.0:
        return weight
    if ratio >= 3.0:
        return 0.0
    return ((3.0 - ratio) / 2.0) * weight


def fatigue_reason(ctr_fatigued: bool, freq_fatigued: bool) -> str:
    """Return a human-readable fatigue reason string."""
    if ctr_fatigued and freq_fatigued:
        return "ctr_drop+high_frequency"
    if ctr_fatigued:
        return "ctr_drop"
    return "high_frequency"
