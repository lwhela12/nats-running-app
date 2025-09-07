from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class FeasibilityResult:
    feasible: bool
    reasons: list[str]
    tradeoffs: list[dict]


def _weeks_between(start: date, end: date) -> int:
    return max(0, (end - start).days // 7)


def assess_feasibility(
    *,
    today: date,
    target_date: date,
    goal_distance_m: int,
    target_time_sec: Optional[int],
    comfortable_distance_m: int,
    comfortable_time_sec: int,
    weekly_volume_cap: float = 0.10,
) -> FeasibilityResult:
    """Simple deterministic feasibility check per MVP guardrails.

    - Derive starting weekly volume ~ 3x comfortable distance.
    - Cap weekly growth at weekly_volume_cap.
    - Long run <= 35% of weekly volume.
    - If time target provided, compare to Riegel prediction and allow modest improvement.
    """
    from .projection import riegel_predict

    reasons: list[str] = []
    tradeoffs: list[dict] = []
    weeks_avail = _weeks_between(today, target_date)
    if weeks_avail < 4:
        reasons.append("Less than 4 weeks available")

    start_weekly_vol = max(comfortable_distance_m * 3.0, 10_000)  # meters
    target_long_run = goal_distance_m * 0.7 if goal_distance_m >= 21_097 else goal_distance_m * 0.5
    # Assume need weekly volume ~ 5-6x long run
    target_weekly_vol = max(target_long_run * 3.0, goal_distance_m * 2.5)

    # Compute weeks needed to reach target volume under cap
    weeks_needed = 0
    vol = start_weekly_vol
    while vol < target_weekly_vol and weeks_needed < 200:
        vol *= (1 + weekly_volume_cap)
        weeks_needed += 1

    # Time feasibility
    time_feasible = True
    time_relax_sec = 0
    if target_time_sec:
        predicted = riegel_predict(comfortable_time_sec, comfortable_distance_m, goal_distance_m)
        # Allow 5% improvement over naive Riegel (with training)
        best_case = int(predicted * 0.95)
        if target_time_sec < best_case:
            time_feasible = False
            time_relax_sec = best_case - target_time_sec
            reasons.append("Target time aggressive vs current fitness")

    feasible = (weeks_needed <= weeks_avail) and time_feasible and (len(reasons) == 0)

    if not feasible:
        # Tradeoff: push date
        push_weeks = max(0, weeks_needed - weeks_avail)
        if push_weeks > 0:
            tradeoffs.append({"lever": "date", "recommendation": {"push_weeks": push_weeks}})
        # Tradeoff: relax time
        if target_time_sec and not time_feasible:
            tradeoffs.append({"lever": "time", "recommendation": {"relax_seconds": time_relax_sec}})
        # Tradeoff: reduce distance (e.g., suggest 10K/HM)
        if goal_distance_m >= 21_097:  # half or full
            alt = 10_000 if goal_distance_m >= 42_195 else 5_000
            tradeoffs.append({"lever": "distance", "recommendation": {"suggest_distance_m": alt}})

    return FeasibilityResult(feasible=feasible, reasons=reasons, tradeoffs=tradeoffs)

