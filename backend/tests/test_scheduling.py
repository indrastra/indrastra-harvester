from datetime import UTC, datetime, timedelta

from backend.app.harvest.schedules import next_occurrence


def test_next_occurrence_uses_utc_interval_frequencies():
    now = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)
    assert next_occurrence("hourly", now) == now + timedelta(hours=1)
    assert next_occurrence("daily", now) == now + timedelta(days=1)
    assert next_occurrence("weekly", now) == now + timedelta(days=7)


def test_next_occurrence_rejects_unknown_frequency():
    now = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)
    try:
        next_occurrence("monthly", now)
    except ValueError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("Unsupported frequency should be rejected.")
