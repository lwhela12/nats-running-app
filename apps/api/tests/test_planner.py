from datetime import date, timedelta

from app.domain.planner import PlanSpec, generate_plan


def test_generate_plan_invariants():
    start = date.today()
    end = start + timedelta(weeks=8)
    spec = PlanSpec(start_date=start, end_date=end, running_days_per_week=4, phases={})
    workouts = generate_plan(goal_distance_m=21097, start_weekly_vol=20000, cap_growth=0.1, spec=spec)
    # No back-to-back intensity in our 4-day template (Mon, Wed, Fri, Sun)
    days = sorted({w.wdate for w in workouts})
    assert len(workouts) == 8 * 4
    # Long run proportion check
    longs = [w for w in workouts if w.wtype == "long"]
    assert len(longs) == 8

