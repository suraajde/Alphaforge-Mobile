"""Unit and navigation test suite for Watchtower Screen (Sprint 14.0.0)."""

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

    # Verify watchtower is instantiated on MainWindow
    assert hasattr(win, "watchtower")
    assert isinstance(win.watchtower, Watchtower)

    # Verify watchtower is added to QStackedWidget
    assert win.pages.indexOf(win.watchtower) != -1

    # Verify sidebar button exists
    assert hasattr(win.sidebar, "watchtower_btn")

    # Simulate sidebar click for Watchtower
    win.sidebar.watchtower_btn.click()

    # Verify current widget switched to watchtower
    assert win.pages.currentWidget() == win.watchtower
