"""Timeframe utilities for working with bounded datetime ranges."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

__all__ = ["Timeframe"]


@dataclass(frozen=True, slots=True)
class Timeframe:
    """A closed-open range between two datetimes."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("end must be greater than or equal to start")

    @classmethod
    def from_point(cls, point: datetime) -> Timeframe:
        """Create a zero-length timeframe at a single point in time."""
        return cls(start=point, end=point)

    @classmethod
    def starting_at(cls, start: datetime, length: timedelta) -> Timeframe:
        """Create a timeframe from its start and length."""
        return cls(start=start, end=start + length)

    @classmethod
    def ending_at(cls, end: datetime, length: timedelta) -> Timeframe:
        """Create a timeframe from its end and length."""
        return cls(start=end - length, end=end)

    @classmethod
    def until(cls, end: datetime) -> Timeframe:
        """Create a timeframe that includes all representable time until end."""
        return cls(start=datetime.min.replace(tzinfo=end.tzinfo), end=end)

    @classmethod
    def around(cls, point: datetime, *, radius: timedelta) -> Timeframe:
        """Create a timeframe centered around a point in time."""
        return cls(start=point - radius, end=point + radius)

    @property
    def length(self) -> timedelta:
        """Return the duration between start and end."""
        return self.end - self.start

    def __contains__(self, point: datetime) -> bool:
        return self.start <= point < self.end

    def overlaps(self, other: Timeframe) -> bool:
        return self.start < other.end and other.start < self.end

    def shift(self, delta: timedelta) -> Timeframe:
        return Timeframe(start=self.start + delta, end=self.end + delta)
