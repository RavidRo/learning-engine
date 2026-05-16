from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learning_engine.timeframe import Timeframe


def test_timeframe_holds_start_and_end_datetimes() -> None:
    start = datetime(2026, 5, 16, 8, 30, tzinfo=UTC)
    end = datetime(2026, 5, 16, 10, 0, tzinfo=UTC)

    timeframe = Timeframe(start=start, end=end)

    assert timeframe.start == start
    assert timeframe.end == end


def test_length_returns_time_between_start_and_end() -> None:
    timeframe = Timeframe(
        start=datetime(2026, 5, 16, 8, 30, tzinfo=UTC),
        end=datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
    )

    assert timeframe.length == timedelta(hours=1, minutes=30)


def test_from_point_creates_zero_length_timeframe() -> None:
    point = datetime(2026, 5, 16, 9, 0, tzinfo=UTC)

    assert Timeframe.from_point(point) == Timeframe(start=point, end=point)


def test_starting_at_creates_timeframe_from_start_and_duration() -> None:
    start = datetime(2026, 5, 16, 9, 0, tzinfo=UTC)

    assert Timeframe.starting_at(start, timedelta(minutes=45)) == Timeframe(
        start=start,
        end=datetime(2026, 5, 16, 9, 45, tzinfo=UTC),
    )


def test_ending_at_creates_timeframe_from_end_and_duration() -> None:
    end = datetime(2026, 5, 16, 9, 45, tzinfo=UTC)

    assert Timeframe.ending_at(end, timedelta(minutes=45)) == Timeframe(
        start=datetime(2026, 5, 16, 9, 0, tzinfo=UTC),
        end=end,
    )


def test_around_creates_symmetric_timeframe_around_point() -> None:
    point = datetime(2026, 5, 16, 9, 0, tzinfo=UTC)

    assert Timeframe.around(point, radius=timedelta(minutes=15)) == Timeframe(
        start=datetime(2026, 5, 16, 8, 45, tzinfo=UTC),
        end=datetime(2026, 5, 16, 9, 15, tzinfo=UTC),
    )


def test_contains_uses_inclusive_start_and_exclusive_end() -> None:
    timeframe = Timeframe(
        start=datetime(2026, 5, 16, 9, 0, tzinfo=UTC),
        end=datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
    )

    assert datetime(2026, 5, 16, 9, 0, tzinfo=UTC) in timeframe
    assert datetime(2026, 5, 16, 9, 59, tzinfo=UTC) in timeframe
    assert datetime(2026, 5, 16, 10, 0, tzinfo=UTC) not in timeframe


def test_overlaps_identifies_shared_time() -> None:
    timeframe = Timeframe(
        start=datetime(2026, 5, 16, 9, 0, tzinfo=UTC),
        end=datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
    )

    assert timeframe.overlaps(
        Timeframe(
            start=datetime(2026, 5, 16, 9, 30, tzinfo=UTC),
            end=datetime(2026, 5, 16, 10, 30, tzinfo=UTC),
        )
    )
    assert not timeframe.overlaps(
        Timeframe(
            start=datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
            end=datetime(2026, 5, 16, 11, 0, tzinfo=UTC),
        )
    )


def test_shift_returns_timeframe_moved_by_delta() -> None:
    timeframe = Timeframe(
        start=datetime(2026, 5, 16, 9, 0, tzinfo=UTC),
        end=datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
    )

    assert timeframe.shift(timedelta(days=1)) == Timeframe(
        start=datetime(2026, 5, 17, 9, 0, tzinfo=UTC),
        end=datetime(2026, 5, 17, 10, 0, tzinfo=UTC),
    )


def test_timeframe_rejects_end_before_start() -> None:
    with pytest.raises(ValueError, match="end must be greater than or equal to start"):
        Timeframe(
            start=datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
            end=datetime(2026, 5, 16, 9, 0, tzinfo=UTC),
        )
