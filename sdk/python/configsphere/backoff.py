"""Exponential backoff with optional jitter for retry delays."""

import random


class BackoffStrategy:
    """Computes exponential backoff delays with optional decorrelated jitter.

    Without jitter: delay = min(max_sec, base_sec * multiplier ^ (attempt - 1))
    With jitter (AWS-style decorrelated): delay = min(max_sec, random(0, prev_delay * multiplier))
    """

    def __init__(
        self,
        base_sec: float,
        multiplier: float,
        max_sec: float,
        jitter: bool = True,
    ):
        self._base_sec = base_sec
        self._multiplier = multiplier
        self._max_sec = max_sec
        self._jitter = jitter
        self._current_attempt = 0
        self._prev_delay = base_sec

    @property
    def current_attempt(self) -> int:
        return self._current_attempt

    def next_delay(self) -> float:
        """Return the next backoff delay in seconds and increment the attempt counter."""
        self._current_attempt += 1

        if self._jitter:
            delay = min(self._max_sec, random.uniform(0, self._prev_delay * self._multiplier))
            self._prev_delay = max(self._base_sec, delay)
        else:
            delay = min(self._max_sec, self._base_sec * (self._multiplier ** (self._current_attempt - 1)))

        return delay

    def reset(self) -> None:
        """Reset backoff state after a successful operation."""
        self._current_attempt = 0
        self._prev_delay = self._base_sec
