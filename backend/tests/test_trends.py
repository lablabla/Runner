from datetime import datetime, timedelta, timezone

from app.services import trends


def _mk(days_ago: int, km: float, hr: float | None = 150, load: float | None = None):
    start = datetime.now(timezone.utc) - timedelta(days=days_ago)
    dist = km * 1000
    dur = km * 300  # 5:00/km
    return {
        "start_time": start,
        "distance_m": dist,
        "duration_s": dur,
        "avg_hr": hr,
        "avg_pace_s_per_km": 300.0,
        "training_load": load,
        "difficulty_score": 50.0,
    }


def test_weekly_mileage_groups_by_week():
    acts = [_mk(1, 10), _mk(2, 8), _mk(9, 12)]
    weekly = trends.weekly_mileage(acts)
    assert len(weekly) >= 2
    assert all("distance_km" in w for w in weekly)


def test_acwr_optimal_zone_for_steady_load():
    # Steady ~30km/week for 4 weeks -> ratio near 1.0.
    acts = [_mk(d, 5) for d in range(0, 28, 1) if d % 2 == 0]
    result = trends.acwr(acts)
    assert result["ratio"] is not None
    assert result["zone"] in {"optimal", "caution", "detraining"}


def test_acwr_flags_spike():
    steady = [_mk(d, 2) for d in range(8, 28)]  # low chronic load
    spike = [_mk(d, 15) for d in range(0, 7)]  # big acute week
    result = trends.acwr(steady + spike)
    assert result["ratio"] > 1.5
    assert result["zone"] == "high-risk"


def test_aerobic_efficiency_returns_series():
    acts = [_mk(d, 6) for d in range(0, 5)]
    series = trends.aerobic_efficiency(acts)
    assert len(series) == 5
    assert all("efficiency_index" in p for p in series)


def test_summary_stats_shape():
    # Include a run today so "this week" is non-empty regardless of week-start config.
    acts = [_mk(0, 10), _mk(3, 8)]
    daily = [{"date": datetime.now(timezone.utc).date(), "sleep_score": 80, "sleep_seconds": 27000,
              "body_battery_high": 90, "training_readiness": 75, "stress_avg": 40, "steps": 10643}]
    stats = trends.summary_stats(acts, daily)
    assert stats["total_runs"] == 2
    assert stats["total_distance_km"] > 0
    assert stats["this_week_km"] > 0  # today's run is always in the current week
    assert "acwr" in stats
    # Recovery panel must surface all captured wellness fields, not just some.
    assert stats["recovery"]["sleep_score"] == 80
    assert stats["recovery"]["sleep_seconds"] == 27000
    assert stats["recovery"]["steps"] == 10643
    assert stats["recovery"]["stress_avg"] == 40


def test_mileage_excludes_non_runs():
    swim = _mk(0, 2)
    swim["sport_type"] = "lap_swimming"
    run = _mk(0, 5)
    run["sport_type"] = "running"
    stats = trends.summary_stats([swim, run], [])
    assert stats["total_runs"] == 1  # swim excluded from run count/mileage
    assert abs(stats["this_week_km"] - 5.0) < 0.01
