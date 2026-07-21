from app.services.difficulty import DifficultyInputs, compute_difficulty


def test_missing_data_returns_zero():
    score, breakdown = compute_difficulty(DifficultyInputs())
    assert score == 0.0
    assert breakdown["note"] == "insufficient data"


def test_easy_run_scores_low():
    score, _ = compute_difficulty(
        DifficultyInputs(
            duration_s=30 * 60,
            distance_m=5000,
            avg_hr=120,
            max_hr_user=190,
            elevation_gain_m=10,
            apparent_temp_c=12,
            body_battery_high=90,
            sleep_score=85,
        )
    )
    assert score < 30


def test_hard_hot_hilly_run_scores_high():
    score, breakdown = compute_difficulty(
        DifficultyInputs(
            duration_s=110 * 60,
            distance_m=21000,
            avg_hr=178,
            max_hr_user=190,
            elevation_gain_m=600,
            apparent_temp_c=30,
            body_battery_high=40,
            sleep_score=45,
        )
    )
    assert score > 65
    assert breakdown["heat"] > 50
    assert breakdown["intensity"] > 50


def test_heat_increases_difficulty():
    base = dict(duration_s=45 * 60, distance_m=8000, avg_hr=150, max_hr_user=190, elevation_gain_m=50)
    cool, _ = compute_difficulty(DifficultyInputs(apparent_temp_c=10, **base))
    hot, _ = compute_difficulty(DifficultyInputs(apparent_temp_c=32, **base))
    assert hot > cool


def test_weights_renormalise_when_components_missing():
    # Only intensity available -> its weight becomes 1.0 and the score maps directly
    # to the intensity component (avg_hr at the top of the 0.55-0.95 band == ~100).
    score, breakdown = compute_difficulty(DifficultyInputs(avg_hr=180.5, max_hr_user=190))
    assert set(breakdown) == {"intensity", "_weights"}
    assert breakdown["_weights"]["intensity"] == 1.0
    assert abs(score - breakdown["intensity"]) < 0.1
