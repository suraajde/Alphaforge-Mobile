import os
import shutil
import tempfile
from pathlib import Path
import pytest

from services.alert_center_service import AlertCenterService, PortfolioAlert
from services.alert_dashboard_service import (
    AlertDashboard,
    AlertDashboardSummary,
    AlertDashboardService,
)


def test_service_instantiation():
    """Verify service instantiation."""
    service = AlertDashboardService()
    assert service is not None


def test_empty_dashboard():
    """Verify build_dashboard returns empty dashboard when no alerts exist."""
    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        empty_file = Path(temp_dir) / "empty.json"
        empty_file.write_text("[]", encoding="utf-8")

        ac_svc = AlertCenterService(storage_path=str(empty_file))
        service = AlertDashboardService(alert_center_service=ac_svc)
        dashboard = service.build_dashboard()

        assert isinstance(dashboard, AlertDashboard)
        assert dashboard.summary.total_alerts == 0
        assert dashboard.summary.active_alerts == 0
        assert dashboard.summary.acknowledged_alerts == 0
        assert dashboard.summary.dismissed_alerts == 0
        assert dashboard.summary.info_alerts == 0
        assert dashboard.summary.low_alerts == 0
        assert dashboard.summary.medium_alerts == 0
        assert dashboard.summary.high_alerts == 0
        assert dashboard.summary.critical_alerts == 0
        assert dashboard.alerts == []
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_missing_alert_file():
    """Verify build_dashboard handles missing alert file gracefully."""
    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        missing_file = Path(temp_dir) / "nonexistent_alerts.json"
        ac_svc = AlertCenterService(storage_path=str(missing_file))
        service = AlertDashboardService(alert_center_service=ac_svc)
        dashboard = service.build_dashboard()

        assert isinstance(dashboard, AlertDashboard)
        assert dashboard.summary.total_alerts == 0
        assert dashboard.alerts == []
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_corrupt_alert_file():
    """Verify build_dashboard handles corrupt JSON alert file gracefully."""
    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    try:
        corrupt_file = Path(temp_dir) / "corrupt.json"
        corrupt_file.write_text("{invalid json structure", encoding="utf-8")

        ac_svc = AlertCenterService(storage_path=str(corrupt_file))
        service = AlertDashboardService(alert_center_service=ac_svc)
        dashboard = service.build_dashboard()

        assert isinstance(dashboard, AlertDashboard)
        assert dashboard.summary.total_alerts == 0
        assert dashboard.alerts == []
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_summary_calculations():
    """Verify summary calculations with multiple alerts across status and severity."""
    alerts_list = [
        PortfolioAlert("1", "2026-08-07 10:00", "TYPE1", "INFO", "Title 1", "Desc 1", "ACTIVE"),
        PortfolioAlert("2", "2026-08-07 10:05", "TYPE2", "LOW", "Title 2", "Desc 2", "ACTIVE"),
        PortfolioAlert("3", "2026-08-07 10:10", "TYPE3", "MEDIUM", "Title 3", "Desc 3", "ACKNOWLEDGED"),
        PortfolioAlert("4", "2026-08-07 10:15", "TYPE4", "HIGH", "Title 4", "Desc 4", "DISMISSED"),
        PortfolioAlert("5", "2026-08-07 10:20", "TYPE5", "CRITICAL", "Title 5", "Desc 5", "ACTIVE"),
    ]

    class MockAlertCenterState:
        def __init__(self, alerts):
            self.total_alerts = len(alerts)
            self.active_alerts = 3
            self.acknowledged_alerts = 1
            self.dismissed_alerts = 1
            self.alerts = alerts

    service = AlertDashboardService()
    dashboard = service.build_dashboard(alert_center_state=MockAlertCenterState(alerts_list))

    assert dashboard.summary.total_alerts == 5
    assert dashboard.summary.active_alerts == 3
    assert dashboard.summary.acknowledged_alerts == 1
    assert dashboard.summary.dismissed_alerts == 1
    assert dashboard.summary.info_alerts == 1
    assert dashboard.summary.low_alerts == 1
    assert dashboard.summary.medium_alerts == 1
    assert dashboard.summary.high_alerts == 1
    assert dashboard.summary.critical_alerts == 1
    assert len(dashboard.alerts) == 5


def test_severity_counts():
    """Verify breakdown of severity counts."""
    alerts_list = [
        PortfolioAlert("1", "2026-08-07", "T1", "HIGH", "A1", "D1", "ACTIVE"),
        PortfolioAlert("2", "2026-08-07", "T2", "HIGH", "A2", "D2", "ACTIVE"),
        PortfolioAlert("3", "2026-08-07", "T3", "CRITICAL", "A3", "D3", "ACTIVE"),
        PortfolioAlert("4", "2026-08-07", "T4", "INFO", "A4", "D4", "ACTIVE"),
    ]

    class MockState:
        def __init__(self, alerts):
            self.alerts = alerts

    service = AlertDashboardService()
    dashboard = service.build_dashboard(alert_center_state=MockState(alerts_list))

    assert dashboard.summary.total_alerts == 4
    assert dashboard.summary.high_alerts == 2
    assert dashboard.summary.critical_alerts == 1
    assert dashboard.summary.info_alerts == 1
    assert dashboard.summary.medium_alerts == 0
    assert dashboard.summary.low_alerts == 0


def test_status_counts():
    """Verify breakdown of status counts."""
    alerts_list = [
        PortfolioAlert("1", "2026-08-07", "T1", "INFO", "A1", "D1", "ACTIVE"),
        PortfolioAlert("2", "2026-08-07", "T2", "INFO", "A2", "D2", "ACTIVE"),
        PortfolioAlert("3", "2026-08-07", "T3", "INFO", "A3", "D3", "ACKNOWLEDGED"),
        PortfolioAlert("4", "2026-08-07", "T4", "INFO", "A4", "D4", "DISMISSED"),
        PortfolioAlert("5", "2026-08-07", "T5", "INFO", "A5", "D5", "DISMISSED"),
    ]

    class MockState:
        def __init__(self, alerts):
            self.alerts = alerts

    service = AlertDashboardService()
    dashboard = service.build_dashboard(alert_center_state=MockState(alerts_list))

    assert dashboard.summary.total_alerts == 5
    assert dashboard.summary.active_alerts == 2
    assert dashboard.summary.acknowledged_alerts == 1
    assert dashboard.summary.dismissed_alerts == 2


def test_dashboard_creation():
    """Verify AlertDashboard and AlertDashboardSummary dataclass attributes."""
    summary = AlertDashboardSummary(
        total_alerts=10,
        active_alerts=5,
        acknowledged_alerts=3,
        dismissed_alerts=2,
        info_alerts=4,
        low_alerts=2,
        medium_alerts=2,
        high_alerts=1,
        critical_alerts=1,
    )
    dashboard = AlertDashboard(summary=summary, alerts=[])
    assert dashboard.summary.total_alerts == 10
    assert dashboard.summary.critical_alerts == 1
    assert dashboard.alerts == []


def test_defensive_exception_handling():
    """Verify service handles exceptions gracefully without throwing."""
    class BrokenAlertCenterState:
        @property
        def alerts(self):
            raise RuntimeError("Broken storage")

    service = AlertDashboardService()
    dashboard = service.build_dashboard(alert_center_state=BrokenAlertCenterState())

    assert isinstance(dashboard, AlertDashboard)
    assert dashboard.summary.total_alerts == 0
    assert dashboard.alerts == []
