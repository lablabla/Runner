import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.services.normalize import normalize_garmin, normalize_strava
from app.services.runna import classify_workout, is_runna_activity


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip():
    token = create_access_token(42)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_jwt_rejects_tampering():
    token = create_access_token(1)
    with pytest.raises(jwt.PyJWTError):
        decode_token(token + "tamper")


def test_runna_detection():
    assert is_runna_activity("Easy Run with Runna ✅")
    assert not is_runna_activity("Morning Run")


def test_workout_classification():
    assert classify_workout("Tempo intervals 4x1km") == "tempo"
    assert classify_workout("Long run 18km") == "long"
    assert classify_workout("Recovery jog") == "easy"


def test_normalize_garmin_minimal():
    raw = {
        "activityId": 123,
        "activityName": "Morning Run with Runna ✅",
        "startTimeGMT": "2026-07-01 06:30:00",
        "activityType": {"typeKey": "running"},
        "distance": 10000,
        "duration": 3000,
        "averageHR": 155,
    }
    norm = normalize_garmin(raw)
    assert norm["source"] == "garmin"
    assert norm["source_id"] == "123"
    assert norm["is_runna"] is True
    assert norm["avg_pace_s_per_km"] == 300.0


def test_normalize_strava_minimal():
    raw = {
        "id": 999,
        "name": "Evening Run",
        "sport_type": "Run",
        "start_date": "2026-07-01T18:00:00Z",
        "distance": 5000,
        "moving_time": 1500,
        "elapsed_time": 1600,
    }
    norm = normalize_strava(raw)
    assert norm["source"] == "strava"
    assert norm["avg_pace_s_per_km"] == 300.0
    assert norm["is_runna"] is False
