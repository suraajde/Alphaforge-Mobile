"""Unit and navigation test suite for Watchtower Screen & Lazy Navigation (Sprint 14.0.1)."""

import pytest
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.screens.watchtower import Watchtower


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_watchtower_initialization(qapp):
    """Verify Watchtower initializes safely with default dependencies."""
    screen = Watchtower()
    assert screen is not None
    assert hasattr(screen, "mon_container")
    assert hasattr(screen, "alert_container")
    assert hasattr(screen, "stab_container")


def test_watchtower_custom_service_injection(qapp):
    """Verify Watchtower initializes with custom injected services."""

    class MockDashService:
        def build_dashboard(self):
            return None

    class MockAlertService:
        def get_state(self):
            return None

    class MockStabService:
        def get_stability(self):
            return None

    screen = Watchtower(
        monitoring_dashboard_service=MockDashService(),
        alert_center_service=MockAlertService(),
        stability_service=MockStabService(),
    )
    assert screen is not None


def test_watchtower_defensive_exception_handling(qapp):
    """Verify Watchtower handles faulty dependency exceptions gracefully without crashing UI."""

    class FaultyService:
        def build_dashboard(self):
            raise RuntimeError("Database breakdown")

        def get_state(self):
            raise RuntimeError("Alert system down")

        def get_stability(self):
            raise RuntimeError("Stability engine fault")

    faulty = FaultyService()
    screen = Watchtower(
        monitoring_dashboard_service=faulty,
        alert_center_service=faulty,
        stability_service=faulty,
    )
    assert screen is not None


def test_watchtower_sidebar_navigation(qapp):
    """Verify Watchtower page is registered on MainWindow and connected to sidebar."""
    win = MainWindow()

    # Verify watchtower is instantiated on demand
    assert win.watchtower is not None
    assert isinstance(win.watchtower, Watchtower)

    # Verify watchtower is added to QStackedWidget
    assert win.pages.indexOf(win.watchtower) != -1

    # Simulate sidebar click for Watchtower
    win.sidebar.watchtower_btn.click()

    # Verify current widget switched to watchtower
    assert win.pages.currentWidget() == win.watchtower


def test_portfolio_opened_before_research_radar(qapp):
    """Verify Portfolio opened before ResearchRadar returns valid current_alpha12 without crash or lost provider link."""
    win = MainWindow()

    # Open portfolio FIRST before research_radar has been visited
    win.sidebar.portfolio_btn.click()
    assert win.pages.currentWidget() == win.portfolio

    # Verify provider function executes cleanly
    candidates = win._current_alpha12()
    assert isinstance(candidates, list)


def test_research_radar_to_portfolio_flow(qapp):
    """Verify Alpha 12 scan result in ResearchRadar flows into Portfolio provider."""
    win = MainWindow()

    # Simulate scan result set on ResearchRadar
    win.research_radar.last_result = {
        "alpha12": [{"symbol": "STOCK1", "score": 90}]
    }

    # Verify _current_alpha12 provider returns updated alpha12 candidates
    candidates = win._current_alpha12()
    assert len(candidates) == 1
    assert candidates[0]["symbol"] == "STOCK1"
