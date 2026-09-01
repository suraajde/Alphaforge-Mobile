"""Unit and navigation test suite for Dashboard Screen (Sprint 14.0.0)."""

import pytest
from PySide6.QtWidgets import QApplication

from app.screens.dashboard import Dashboard


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_dashboard_initialization(qapp):
    """Verify Dashboard initializes safely with default dependencies."""
    screen = Dashboard()
    assert screen is not None
    assert hasattr(screen, "lbl_health_val")
    assert hasattr(screen, "lbl_val_val")
    assert hasattr(screen, "lbl_stab_val")
    assert hasattr(screen, "lbl_alerts_val")


def test_dashboard_custom_service_injection(qapp):
    """Verify Dashboard initializes with custom injected services."""

    class MockHealthService:
        def evaluate(self, snapshot=None):
            return None

        def build_snapshot(self):
            return None

    class MockStabService:
        def get_stability(self):
            return None

    class MockAlertService:
        def get_state(self):
            return None

    screen = Dashboard(
        portfolio_health_service=MockHealthService(),
        alpha12_stability_service=MockStabService(),
        alert_center_service=MockAlertService(),
    )
    assert screen is not None


def test_dashboard_defensive_exception_handling(qapp):
    """Verify Dashboard handles faulty dependency exceptions gracefully without crashing UI."""

    class FaultyService:
        def evaluate(self, snapshot=None):
            raise RuntimeError("Evaluation failure")

        def build_snapshot(self):
            raise RuntimeError("Snapshot failure")

        def get_stability(self):
            raise RuntimeError("Stability failure")

        def get_state(self):
            raise RuntimeError("Alert failure")

        def load_state(self, path=None):
            raise RuntimeError("State load failure")

    faulty = FaultyService()
    screen = Dashboard(
        portfolio_health_service=faulty,
        alpha12_stability_service=faulty,
        alert_center_service=faulty,
        portfolio_state_service=faulty,
    )
    assert screen is not None
    assert screen.lbl_health_val.text() in ("N/A", "Unavailable")
    assert screen.lbl_val_val.text() in ("Rs. 0.00", "Unavailable")


def test_dashboard_pnl_and_portfolio_value_positive_pnl(qapp):
    """Verify Dashboard calculates positive P&L and applies green (#00C853) styling."""
    class MockPortfolioStateService:
        def load_state(self, path=None):
            return {
                "status": "OK",
                "state": {
                    "total_portfolio_value": 150000.0,
                    "invested_market_value": 130000.0,
                    "cash_balance": 20000.0,
                    "positions": {
                        "INFY": {
                            "symbol": "INFY",
                            "invested_cost": 100000.0,
                            "current_value": 130000.0,
                        },
                    },
                },
            }

    screen = Dashboard(portfolio_state_service=MockPortfolioStateService())
    screen.refresh_data()

    assert screen.lbl_val_val.text() == "Rs. 150,000.00"
    assert screen.lbl_portfolio_value.text() == "Rs. 150,000.00"
    assert screen.lbl_total_pnl_val.text() == "Rs. 30,000.00 (+30.00%)"
    assert screen.lbl_running_pnl.text() == "Rs. 30,000.00 (+30.00%)"
    assert "#00C853" in screen.lbl_total_pnl_val.styleSheet()


def test_dashboard_pnl_and_portfolio_value_negative_pnl(qapp):
    """Verify Dashboard calculates negative P&L and applies red (#FF3D00) styling."""
    class MockPortfolioStateService:
        def load_state(self, path=None):
            return {
                "status": "OK",
                "state": {
                    "total_portfolio_value": 90000.0,
                    "invested_market_value": 80000.0,
                    "cash_balance": 10000.0,
                    "positions": {
                        "TCS": {
                            "symbol": "TCS",
                            "invested_cost": 100000.0,
                            "current_value": 80000.0,
                        },
                    },
                },
            }

    screen = Dashboard(portfolio_state_service=MockPortfolioStateService())
    screen.refresh_data()

    assert screen.lbl_val_val.text() == "Rs. 90,000.00"
    assert screen.lbl_portfolio_value.text() == "Rs. 90,000.00"
    assert screen.lbl_total_pnl_val.text() == "Rs. -20,000.00 (-20.00%)"
    assert screen.lbl_running_pnl.text() == "Rs. -20,000.00 (-20.00%)"
    assert "#FF3D00" in screen.lbl_total_pnl_val.styleSheet()


def test_main_window_navigation_refreshes_dashboard(qapp):
    """Verify MainWindow navigation to dashboard triggers refresh_data."""
    from unittest.mock import MagicMock
    from app.main_window import MainWindow

    win = MainWindow()
    dashboard = win.dashboard
    dashboard.refresh_data = MagicMock()

    win.navigate_to("stock_explorer")
    assert win.pages.currentWidget() == win.stock_explorer

    win.navigate_to("dashboard")
    assert win.pages.currentWidget() == dashboard
    dashboard.refresh_data.assert_called()

    dashboard.refresh_data.reset_mock()
    win.switch_to_dashboard()
    assert win.pages.currentWidget() == dashboard
    dashboard.refresh_data.assert_called_once()

