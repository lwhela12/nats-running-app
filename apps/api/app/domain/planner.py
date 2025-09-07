from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class PlanSpec:
    start_date: date
    end_date: date
    running_days_per_week: int
    phases: dict  # e.g., {"base":0.5,"build":0.3,"peak":0.1,"taper":0.1}


@dataclass
class WorkoutSpec:
    wdate: date
    wtype: str
    target_distance_m: Optional[int]
    target_duration_sec: Optional[int]
    target_zone: Optional[str]
    description: str
    is_key: bool


def _weeks_between(start: date, end: date) -> int:
    return max(1, (end - start).days // 7)


def _insert_cutbacks(weekly_volumes: List[float]) -> List[float]:
    out: List[float] = []
    for i, v in enumerate(weekly_volumes):
        out.append(v)
        if (i + 1) % 3 == 0 and i + 1 < len(weekly_volumes):
            out.append(max(v * 0.8, 0))
    return out[: len(weekly_volumes)]


def generate_plan(
    *,
    goal_distance_m: int,
    start_weekly_vol: float,
    cap_growth: float,
    spec: PlanSpec,
) -> List[WorkoutSpec]:
    weeks = _weeks_between(spec.start_date, spec.end_date)
    # Build weekly volumes respecting cap and insert cutbacks
    vols: List[float] = []
    v = start_weekly_vol
    for _ in range(weeks):
        vols.append(v)
        v = v * (1 + cap_growth)
    vols = _insert_cutbacks(vols)

    # Simple weekly templates: 4 days run: Mon Easy, Wed Quality, Fri Easy, Sun Long
    weekday_offsets = [0, 2, 4, 6]  # Mon, Wed, Fri, Sun
    workouts: List[WorkoutSpec] = []
    cur = spec.start_date
    for w in range(weeks):
        week_vol = vols[w]
        long_run = min(goal_distance_m * 0.35, week_vol * 0.35)
        quality = min(week_vol * 0.25, long_run * 0.8)
        easy_total = max(0.0, week_vol - long_run - quality)

        days = [cur + timedelta(days=o) for o in weekday_offsets]
        # Easy
        workouts.append(
            WorkoutSpec(
                wdate=days[0],
                wtype="easy",
                target_distance_m=int(easy_total * 0.4),
                target_duration_sec=None,
                target_zone="easy",
                description="Easy run",
                is_key=False,
            )
        )
        # Quality (tempo/interval alternate)
        wtype = "tempo" if (w % 2 == 0) else "interval"
        workouts.append(
            WorkoutSpec(
                wdate=days[1],
                wtype=wtype,
                target_distance_m=int(quality),
                target_duration_sec=None,
                target_zone="threshold" if wtype == "tempo" else "interval",
                description="Quality session",
                is_key=True,
            )
        )
        # Easy 2
        workouts.append(
            WorkoutSpec(
                wdate=days[2],
                wtype="easy",
                target_distance_m=int(easy_total * 0.6),
                target_duration_sec=None,
                target_zone="easy",
                description="Easy run",
                is_key=False,
            )
        )
        # Long
        workouts.append(
            WorkoutSpec(
                wdate=days[3],
                wtype="long",
                target_distance_m=int(long_run),
                target_duration_sec=None,
                target_zone="aerobic",
                description="Long run",
                is_key=True,
            )
        )
        cur = cur + timedelta(days=7)

    # Ensure no back-to-back intensity: our template already spaces them.
    return workouts

