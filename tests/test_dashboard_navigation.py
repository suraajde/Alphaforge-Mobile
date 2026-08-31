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

    faulty = FaultyService()
    screen = Dashboard(
        portfolio_health_service=faulty,
        alpha12_stability_service=faulty,
        alert_center_service=faulty,
    )
    assert screen is not None
    assert screen.lbl_health_val.text() in ("N/A", "Unavailable")
    assert screen.lbl_val_val.text() in ("Rs. 0.00", "Unavailable")
