import pytest

from configsphere.backoff import BackoffStrategy


class TestBackoffStrategy:
    def test_first_delay_equals_base(self):
        strategy = BackoffStrategy(
            base_sec=1.0, multiplier=2.0, max_sec=300.0, jitter=False
        )
        assert strategy.next_delay() == 1.0

    def test_exponential_growth(self):
        strategy = BackoffStrategy(
            base_sec=1.0, multiplier=2.0, max_sec=300.0, jitter=False
        )
        delays = [strategy.next_delay() for _ in range(5)]
        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_caps_at_max(self):
        strategy = BackoffStrategy(
            base_sec=1.0, multiplier=2.0, max_sec=10.0, jitter=False
        )
        delays = [strategy.next_delay() for _ in range(10)]
        assert all(d <= 10.0 for d in delays)
        assert delays[-1] == 10.0

    def test_reset(self):
        strategy = BackoffStrategy(
            base_sec=1.0, multiplier=2.0, max_sec=300.0, jitter=False
        )
        strategy.next_delay()
        strategy.next_delay()
        strategy.reset()
        assert strategy.next_delay() == 1.0
        assert strategy.current_attempt == 1

    def test_current_attempt_tracks_calls(self):
        strategy = BackoffStrategy(
            base_sec=1.0, multiplier=2.0, max_sec=300.0, jitter=False
        )
        assert strategy.current_attempt == 0
        strategy.next_delay()
        assert strategy.current_attempt == 1
        strategy.next_delay()
        assert strategy.current_attempt == 2

    def test_jitter_within_bounds(self):
        strategy = BackoffStrategy(
            base_sec=1.0, multiplier=2.0, max_sec=300.0, jitter=True
        )
        for _ in range(100):
            strategy.reset()
            delay = strategy.next_delay()
            assert 0 <= delay <= 2.0

    def test_jitter_delays_never_exceed_max(self):
        strategy = BackoffStrategy(
            base_sec=1.0, multiplier=2.0, max_sec=5.0, jitter=True
        )
        for _ in range(50):
            delay = strategy.next_delay()
            assert delay <= 5.0

    def test_custom_multiplier(self):
        strategy = BackoffStrategy(
            base_sec=0.5, multiplier=3.0, max_sec=100.0, jitter=False
        )
        delays = [strategy.next_delay() for _ in range(4)]
        assert delays == [0.5, 1.5, 4.5, 13.5]
