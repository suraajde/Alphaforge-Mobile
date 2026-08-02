import pytest

from services.portfolio_performance_service import (
    PortfolioPerformanceService,
    PortfolioPerformanceSnapshot,
)


def test_calculate_performance_basic_gain():
    svc = PortfolioPerformanceService()
    snapshot = svc.calculate_performance(
        initial_value=100000.0,
        current_value=120000.0,
        initial_benchmark=1000.0,
        current_benchmark=1100.0,
    )

    assert isinstance(snapshot, PortfolioPerformanceSnapshot)
    assert snapshot.initial_value == 100000.0
    assert snapshot.current_value == 120000.0
    assert snapshot.absolute_return == 20000.0
    assert pytest.approx(snapshot.absolute_return_pct, 0.01) == 20.0
    assert snapshot.initial_benchmark == 1000.0
    assert snapshot.current_benchmark == 1100.0
    assert pytest.approx(snapshot.benchmark_return_pct, 0.01) == 10.0
    assert pytest.approx(snapshot.alpha_pct, 0.01) == 10.0
    assert pytest.approx(snapshot.growth_multiple, 0.01) == 1.20
    assert snapshot.xirr_pct is None
    assert len(snapshot.warnings) == 0


def test_calculate_performance_loss():
    svc = PortfolioPerformanceService()
    snapshot = svc.calculate_performance(
        initial_value=100000.0,
        current_value=85000.0,
        initial_benchmark=1000.0,
        current_benchmark=950.0,
    )

    assert snapshot.absolute_return == -15000.0
    assert pytest.approx(snapshot.absolute_return_pct, 0.01) == -15.0
    assert pytest.approx(snapshot.benchmark_return_pct, 0.01) == -5.0
    assert pytest.approx(snapshot.alpha_pct, 0.01) == -10.0
    assert pytest.approx(snapshot.growth_multiple, 0.01) == 0.85
    assert len(snapshot.warnings) == 0


def test_zero_initial_value_handling():
    svc = PortfolioPerformanceService()
    snapshot = svc.calculate_performance(
        initial_value=0.0,
        current_value=50000.0,
    )

    assert snapshot.absolute_return == 50000.0
    assert snapshot.absolute_return_pct == 0.0
    assert snapshot.growth_multiple == 0.0
    assert len(snapshot.warnings) > 0
    assert "Initial portfolio value must be greater than 0" in snapshot.warnings[0]


def test_missing_benchmark_handling():
    svc = PortfolioPerformanceService()
    snapshot = svc.calculate_performance(
        initial_value=50000.0,
        current_value=60000.0,
        initial_benchmark=0.0,
        current_benchmark=0.0,
    )

    assert pytest.approx(snapshot.absolute_return_pct, 0.01) == 20.0
    assert snapshot.benchmark_return_pct == 0.0
    assert pytest.approx(snapshot.alpha_pct, 0.01) == 20.0


def test_xirr_placeholder():
    svc = PortfolioPerformanceService()
    # Test placeholder returns None
    assert svc.calculate_xirr() is None
    assert svc.calculate_xirr([("2026-01-01", -10000), ("2026-06-01", 12000)]) is None
