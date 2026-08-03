"""Clock abstractions used by the deterministic simulator and safety checks."""

from __future__ import annotations

import time


class MonotonicClock:
    """Production-process monotonic clock; it is not a wall-clock source."""

    @staticmethod
    def now_ns() -> int:
        return time.monotonic_ns()


class DeterministicClock:
    """Manually advanced clock for replayable tests and scenarios."""

    def __init__(self, initial_ns: int = 0) -> None:
        if initial_ns < 0:
            raise ValueError("initial_ns must be non-negative")
        self._now_ns = int(initial_ns)

    def now_ns(self) -> int:
        return self._now_ns

    def advance_ns(self, amount_ns: int) -> int:
        if amount_ns < 0:
            raise ValueError("clock cannot move backwards")
        self._now_ns += int(amount_ns)
        return self._now_ns

    def set_ns(self, timestamp_ns: int) -> int:
        if timestamp_ns < self._now_ns:
            raise ValueError("clock cannot move backwards")
        self._now_ns = int(timestamp_ns)
        return self._now_ns
