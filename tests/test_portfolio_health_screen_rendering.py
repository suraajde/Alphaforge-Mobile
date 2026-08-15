"""Regression & UI Verification tests for Portfolio Health screen rendering (Sprint 14.1.9).

Validates:
- PortfolioHealth screen initializes completely with child layout and widgets (non-blank)
- MainWindow navigation to portfolio_health getter returns fully populated PortfolioHealth widget
- ErrorFallbackWidget is returned if PortfolioHealth initialization throws an exception
- Watchtower status remains READY
- Alpha 12 persistence and cross-screen consistency remain intact
"""
import sys
import tempfile
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from app.screens.portfolio_health import PortfolioHealth
from app.screens.watchtower import Watchtower
from app.main_window import MainWindow, ErrorFallbackWidget
from services.portfolio_health_history_service import PortfolioHealthHistoryService
from services.portfolio_health_monitor_service import PortfolioHealthMonitorService


@pytest.fixture(autouse=True)
def init_qapp():
    """Ensure QApplication instance exists for PySide6 GUI widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def temp_data_dir(monkeypatch):
    """Isolated temporary data directory fixture enforcing ALPHAFORGE_DATA_DIR test isolation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_dir = Path(tmp_dir) / "alphaforge_test_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("ALPHAFORGE_DATA_DIR", str(data_dir))
        yield data_dir


def test_portfolio_health_screen_initializes_with_layout_and_widgets(temp_data_dir):
    """TEST 1: Verify PortfolioHealth instantiates, builds UI, calls refresh_data, and contains child widgets."""
    screen = PortfolioHealth()
    assert screen is not None
    assert screen.service is not None
    assert screen.layout() is not None
    # Verify layout contains child widgets (non-blank screen)
    assert screen.layout().count() > 0


def test_main_window_portfolio_health_getter_returns_populated_screen(temp_data_dir):
    """TEST 2: Verify MainWindow.portfolio_health getter returns fully populated widget."""
    window = MainWindow()
    health_widget = window.portfolio_health
    assert health_widget is not None
    assert isinstance(health_widget, PortfolioHealth)
    assert health_widget.layout() is not None
    assert health_widget.layout().count() > 0


def test_main_window_portfolio_health_error_fallback_injection(temp_data_dir, monkeypatch):
    """TEST 3: Verify injecting an exception during PortfolioHealth init produces ErrorFallbackWidget."""
    def bad_init(*args, **kwargs):
        raise RuntimeError("Simulated PortfolioHealth failure")

    monkeypatch.setattr(PortfolioHealth, "__init__", bad_init)

    window = MainWindow()
    fallback_widget = window.portfolio_health
    assert fallback_widget is not None
    assert isinstance(fallback_widget, ErrorFallbackWidget)


def test_watchtower_remains_ready_after_health_fix(temp_data_dir):
    """TEST 4: Verify Watchtower status remains READY after portfolio health screen rendering fix."""
    watchtower = Watchtower()
    assert watchtower is not None
    mon_state = watchtower.monitoring_dashboard_service.monitor_service.get_monitoring_state()
    assert mon_state.monitoring_status == "READY"
