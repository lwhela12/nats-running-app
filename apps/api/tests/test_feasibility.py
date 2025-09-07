from datetime import date, timedelta

from app.domain.feasibility import assess_feasibility


def test_feasible_basic_distance_goal():
    today = date.today()
    res = assess_feasibility(
        today=today,
        target_date=today + timedelta(weeks=16),
        goal_distance_m=10000,
        target_time_sec=None,
        comfortable_distance_m=5000,
        comfortable_time_sec=30 * 60,
    )
    assert res.feasible is True


def test_tradeoff_when_too_soon():
    today = date.today()
    res = assess_feasibility(
        today=today,
        target_date=today + timedelta(weeks=3),
        goal_distance_m=21097,
        target_time_sec=None,
        comfortable_distance_m=3000,
        comfortable_time_sec=18 * 60,
    )
    assert res.feasible is False
    assert any(t["lever"] == "date" for t in res.tradeoffs)

