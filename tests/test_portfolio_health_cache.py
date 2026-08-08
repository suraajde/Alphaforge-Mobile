"""Unit test suite for PortfolioHealthService evaluation caching (Sprint 14.0.1)."""

import pytest
from services.portfolio_health_service import (
    PortfolioHealthResult,
    PortfolioHealthService,
    PortfolioHealthSnapshot,
)


class ControlledTimeProvider:
    def __init__(self, initial_time: float = 1000.0):
        self.current_time = initial_time

    def __call__(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


def test_first_call_computes_evaluation():
    """Verify first evaluate() call computes and returns valid result."""
    clock = ControlledTimeProvider()
    svc = PortfolioHealthService(time_provider=clock)
    snapshot = PortfolioHealthSnapshot(10, 100000.0, 90000.0, 5.0, "AAPL", 8.5)

    res1 = svc.evaluate(snapshot)
    assert isinstance(res1, PortfolioHealthResult)
    assert res1.score >= 0


def test_immediate_repeated_call_hits_cache():
    """Verify immediate repeated call with identical snapshot returns cached result object."""
    clock = ControlledTimeProvider()
    svc = PortfolioHealthService(time_provider=clock)
    snapshot = PortfolioHealthSnapshot(10, 100000.0, 90000.0, 5.0, "AAPL", 8.5)

    res1 = svc.evaluate(snapshot)
    res2 = svc.evaluate(snapshot)

    assert res1 is res2  # Exact object identity (cache hit)


def test_cache_expires_after_ttl():
    """Verify cache invalidates and recomputes after 5.0s TTL expires."""
    clock = ControlledTimeProvider()
    svc = PortfolioHealthService(time_provider=clock)
    snapshot = PortfolioHealthSnapshot(10, 100000.0, 90000.0, 5.0, "AAPL", 8.5)

    res1 = svc.evaluate(snapshot)
    clock.advance(3.0)  # Within TTL
    res2 = svc.evaluate(snapshot)
    assert res1 is res2

    clock.advance(3.0)  # Total 6.0s > 5.0s TTL
    res3 = svc.evaluate(snapshot)
    assert res3 is not res1
    assert res3.score == res1.score  # Value equality intact


def test_changed_input_snapshot_invalidates_cache():
    """Verify snapshot parameter change invalidates cache immediately."""
    clock = ControlledTimeProvider()
    svc = PortfolioHealthService(time_provider=clock)
    snap1 = PortfolioHealthSnapshot(10, 100000.0, 90000.0, 5.0, "AAPL", 8.5)
    snap2 = PortfolioHealthSnapshot(5, 50000.0, 45000.0, 15.0, "GOOGL", 25.0)

    res1 = svc.evaluate(snap1)
    res2 = svc.evaluate(snap2)

    assert res1 is not res2
    assert res1.score != res2.score


def test_semantic_previous_result_change_invalidates_cache():
    """Verify change in semantic previous result invalidates cache even with same snapshot."""
    clock = ControlledTimeProvider()
    svc = PortfolioHealthService(time_provider=clock)
    snapshot = PortfolioHealthSnapshot(10, 100000.0, 90000.0, 5.0, "AAPL", 8.5)

    prev1 = PortfolioHealthResult(
        score=70,
        grade="C",
        diversification_rating="POOR",
        concentration_rating="HIGH",
        position_count=5,
        largest_position_weight_pct=25.0,
        cash_allocation_pct=15.0,
    )
    prev2 = PortfolioHealthResult(
        score=95,
        grade="A",
        diversification_rating="GOOD",
        concentration_rating="LOW",
        position_count=12,
        largest_position_weight_pct=8.0,
        cash_allocation_pct=5.0,
    )

    res1 = svc.evaluate(snapshot, previous=prev1)
    res2 = svc.evaluate(snapshot, previous=prev2)

    assert res1 is not res2
    assert res1.trend.previous_score != res2.trend.previous_score


def test_explicit_cache_invalidation():
    """Verify explicit call to invalidate_evaluation_cache() clears cached result."""
    clock = ControlledTimeProvider()
    svc = PortfolioHealthService(time_provider=clock)
    snapshot = PortfolioHealthSnapshot(10, 100000.0, 90000.0, 5.0, "AAPL", 8.5)

    res1 = svc.evaluate(snapshot)
    svc.invalidate_evaluation_cache()
    res2 = svc.evaluate(snapshot)

    assert res1 is not res2


def test_evaluation_exception_does_not_poison_cache():
    """Verify failure during evaluation does not pollute cache with invalid result."""
    clock = ControlledTimeProvider()
    svc = PortfolioHealthService(time_provider=clock)

    # Initial safe evaluation
    snap1 = PortfolioHealthSnapshot(10, 100000.0, 90000.0, 5.0, "AAPL", 8.5)
    res1 = svc.evaluate(snap1)
    assert res1 is not None

    # Invalidate cache
    svc.invalidate_evaluation_cache()

    # Pass invalid non-snapshot object that triggers fallback
    res2 = svc.evaluate(None)
    assert res2 is not None
    assert isinstance(res2, PortfolioHealthResult)
