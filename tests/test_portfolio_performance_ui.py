import pytest
from PySide6.QtWidgets import QApplication

from app.screens.portfolio import Portfolio
from services.portfolio_performance_service import PortfolioPerformanceSnapshot


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_benchmark_summary_outperforming(qapp):
    screen = Portfolio()
    bm_summary = {
        "status": "BEATING_BENCHMARK",
        "portfolio_return_1y": 18.00,
        "benchmark_return_1y": 10.00,
        "alpha_return_1y": 8.00,
    }
    summary = {
        "total_cost": 100000.0,
        "portfolio_value": 118000.0,
    }

    screen._render_benchmark_summary(bm_summary, summary)

    assert screen.bm_portfolio_return_value.text() == "+18.00%"
    assert screen.bm_nifty_return_value.text() == "+10.00%"
    assert screen.bm_alpha_return_value.text() == "+8.00%"
    assert screen.bm_status_value.text() == "OUTPERFORMING"
    assert screen.snapshots_value.text() == "1.18x"


def test_benchmark_summary_underperforming(qapp):
    screen = Portfolio()
    bm_summary = {
        "status": "LAGGING_BENCHMARK",
        "portfolio_return_1y": -3.20,
        "benchmark_return_1y": 5.00,
        "alpha_return_1y": -8.20,
    }
    summary = {
        "total_cost": 100000.0,
        "portfolio_value": 96800.0,
    }

    screen._render_benchmark_summary(bm_summary, summary)

    assert screen.bm_portfolio_return_value.text() == "-3.20%"
    assert screen.bm_nifty_return_value.text() == "+5.00%"
    assert screen.bm_alpha_return_value.text() == "-8.20%"
    assert screen.bm_status_value.text() == "UNDERPERFORMING"
    assert screen.snapshots_value.text() == "0.97x"


def test_benchmark_summary_inline(qapp):
    screen = Portfolio()
    bm_summary = {
        "status": "BEATING_BENCHMARK",
        "portfolio_return_1y": 10.00,
        "benchmark_return_1y": 10.00,
        "alpha_return_1y": 0.00,
    }
    summary = {
        "total_cost": 100000.0,
        "portfolio_value": 110000.0,
    }

    screen._render_benchmark_summary(bm_summary, summary)

    assert screen.bm_portfolio_return_value.text() == "+10.00%"
    assert screen.bm_nifty_return_value.text() == "+10.00%"
    assert screen.bm_alpha_return_value.text() == "+0.00%"
    assert screen.bm_status_value.text() == "INLINE"
    assert screen.snapshots_value.text() == "1.10x"


def test_growth_multiple_formatting_examples(qapp):
    screen = Portfolio()

    for mult, expected in [(1.18, "1.18x"), (1.35, "1.35x"), (2.01, "2.01x"), (0.85, "0.85x")]:
        snapshot = PortfolioPerformanceSnapshot(
            initial_value=100.0,
            current_value=100.0 * mult,
            absolute_return=(mult - 1) * 100.0,
            absolute_return_pct=(mult - 1) * 100.0,
            initial_benchmark=0.0,
            current_benchmark=0.0,
            benchmark_return_pct=0.0,
            alpha_pct=0.0,
            growth_multiple=mult,
        )
        screen._render_performance_snapshot(snapshot)
        assert screen.snapshots_value.text() == expected
