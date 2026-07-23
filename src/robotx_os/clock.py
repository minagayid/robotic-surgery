"""Injectable monotonic clocks for production and deterministic replay."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic_ns
from typing import Protocol


class Clock(Protocol):
    def now_ns(self) -> int: ...


class SystemMonotonicClock:
    def now_ns(self) -> int:
        return monotonic_ns()


@dataclass(slots=True)
class ManualClock:
    current_ns: int = 0

    def now_ns(self) -> int:
        return self.current_ns

    def advance_ns(self, duration_ns: int) -> int:
        if duration_ns < 0:
            raise ValueError("manual clock cannot move backwards")
        self.current_ns += duration_ns
        return self.current_ns
