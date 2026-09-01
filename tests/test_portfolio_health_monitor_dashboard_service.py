import json
import shutil
import tempfile
from pathlib import Path
import pytest

from services.portfolio_health_history_service import (
    PortfolioHealthHistoryEntry,
    PortfolioHealthHistoryService,
)
from services.portfolio_health_monitor_dashboard_service import (
    PortfolioHealthMonitoringDashboard,
    PortfolioHealthMonitoringDashboardService,
)
from services.portfolio_health_monitor_service import PortfolioHealthMonitorService
from services.portfolio_health_timeline_service import PortfolioHealthTimelineService


@pytest.fixture
def custom_tmp_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_service_instantiation():
    """Verify service instantiation."""
    service = PortfolioHealthMonitoringDashboardService()
    assert service is not None


def test_dashboard_creation(custom_tmp_dir):
    """Verify build_dashboard returns a valid PortfolioHealthMonitoringDashboard."""
    file_path = custom_tmp_dir / "history.json"
    data = [
        {
            "timestamp": "2026-08-07T08:00:00Z",
            "score": 84,
            "grade": "B",
            "diversification_rating": "GOOD",
            "concentration_rating": "MODERATE",
            "position_count": 10,
            "largest_position_weight_pct": 12.0,
            "cash_allocation_pct": 8.0,
            "largest_position": "INFY",
        },
        {
            "timestamp": "2026-08-08T09:15:00Z",
            "score": 91,
            "grade": "A",
            "diversification_rating": "GOOD",
            "concentration_rating": "LOW",
            "position_count": 12,
            "largest_position_weight_pct": 8.0,
            "cash_allocation_pct": 5.0,
            "largest_position": "TCS",
        },
    ]
    file_path.write_text(json.dumps(data), encoding="utf-8")

    hist_svc = PortfolioHealthHistoryService(storage_path=str(file_path))
    service = PortfolioHealthMonitoringDashboardService(history_service=hist_svc)

    dashboard = service.build_dashboard()
    assert isinstance(dashboard, PortfolioHealthMonitoringDashboard)
    assert dashboard.monitoring_status == "READY"
    assert dashboard.monitoring_enabled is True
    assert dashboard.latest_score == 91
    assert dashboard.latest_grade == "A"
    assert dashboard.latest_snapshot_time == "2026-08-08T09:15:00Z"
    assert dashboard.total_snapshots == 2
    assert dashboard.timeline_entries == 2
    assert dashboard.latest_change_count > 0
    assert dashboard.total_detected_changes > 0


def test_monitoring_integration(custom_tmp_dir):
    """Verify integration with PortfolioHealthMonitorService."""
    file_path = custom_tmp_dir / "history.json"
    data = [
        {
            "timestamp": "2026-08-08T09:15:00Z",
            "score": 91,
            "grade": "A",
            "diversification_rating": "GOOD",
            "concentration_rating": "LOW",
            "position_count": 12,
            "largest_position_weight_pct": 8.0,
            "cash_allocation_pct": 5.0,
            "largest_position": "TCS",
        }
    ]
    file_path.write_text(json.dumps(data), encoding="utf-8")

    hist_svc = PortfolioHealthHistoryService(storage_path=str(file_path))
    mon_svc = PortfolioHealthMonitorService(history_service=hist_svc)
    service = PortfolioHealthMonitoringDashboardService(history_service=hist_svc, monitor_service=mon_svc)

    dashboard = service.build_dashboard()
    assert dashboard.monitoring_status == "READY"
    assert dashboard.monitoring_enabled is True
    assert dashboard.latest_score == 91
    assert dashboard.latest_grade == "A"


def test_timeline_and_change_detection_integration(custom_tmp_dir):
    """Verify integration with timeline and change detection."""
    file_path = custom_tmp_dir / "history.json"
    data = [
        {
            "timestamp": "2026-07-01T10:00:00Z",
            "score": 80,
            "grade": "B",
            "diversification_rating": "GOOD",
            "concentration_rating": "MODERATE",
            "position_count": 10,
            "largest_position_weight_pct": 12.0,
            "cash_allocation_pct": 8.0,
            "largest_position": "INFY",
        },
        {
            "timestamp": "2026-07-15T10:00:00Z",
            "score": 84,
            "grade": "B",
            "diversification_rating": "GOOD",
            "concentration_rating": "MODERATE",
            "position_count": 12,
            "largest_position_weight_pct": 12.0,
            "cash_allocation_pct": 8.0,
            "largest_position": "INFY",
        },
        {
            "timestamp": "2026-08-08T10:00:00Z",
            "score": 91,
            "grade": "A",
            "diversification_rating": "GOOD",
            "concentration_rating": "LOW",
            "position_count": 12,
            "largest_position_weight_pct": 8.0,
            "cash_allocation_pct": 5.0,
            "largest_position": "TCS",
        },
    ]
    file_path.write_text(json.dumps(data), encoding="utf-8")

    hist_svc = PortfolioHealthHistoryService(storage_path=str(file_path))
    service = PortfolioHealthMonitoringDashboardService(history_service=hist_svc)

    dashboard = service.build_dashboard()
    assert dashboard.total_snapshots == 3
    assert dashboard.timeline_entries == 3
    assert dashboard.latest_change_count > 0
    assert dashboard.total_detected_changes >= dashboard.latest_change_count


def test_missing_history_safety(custom_tmp_dir):
    """Verify dashboard safety when history file is missing."""
    missing_file = str(custom_tmp_dir / "missing.json")
    hist_svc = PortfolioHealthHistoryService(storage_path=missing_file)
    service = PortfolioHealthMonitoringDashboardService(history_service=hist_svc)

    dashboard = service.build_dashboard()
    assert dashboard.monitoring_status == "UNAVAILABLE"
    assert dashboard.monitoring_enabled is False
    assert dashboard.latest_score == 0
    assert dashboard.latest_grade == "-"
    assert dashboard.latest_snapshot_time is None
    assert dashboard.total_snapshots == 0
    assert dashboard.total_detected_changes == 0
    assert dashboard.latest_change_count == 0
    assert dashboard.timeline_entries == 0


def test_empty_history_safety(custom_tmp_dir):
    """Verify dashboard safety when history file is empty."""
    empty_file = custom_tmp_dir / "empty.json"
    empty_file.write_text("[]", encoding="utf-8")

    hist_svc = PortfolioHealthHistoryService(storage_path=str(empty_file))
    service = PortfolioHealthMonitoringDashboardService(history_service=hist_svc)

    dashboard = service.build_dashboard()
    assert dashboard.monitoring_status == "WAITING"
    assert dashboard.monitoring_enabled is True
    assert dashboard.total_snapshots == 0
    assert dashboard.total_detected_changes == 0
    assert dashboard.latest_change_count == 0
    assert dashboard.timeline_entries == 0


def test_corrupt_history_safety(custom_tmp_dir):
    """Verify dashboard safety when history file is corrupt."""
    corrupt_file = custom_tmp_dir / "corrupt.json"
    corrupt_file.write_text("INVALID_JSON{", encoding="utf-8")

    hist_svc = PortfolioHealthHistoryService(storage_path=str(corrupt_file))
    service = PortfolioHealthMonitoringDashboardService(history_service=hist_svc)

    dashboard = service.build_dashboard()
    assert dashboard.monitoring_status == "UNAVAILABLE"
    assert dashboard.monitoring_enabled is False
    assert dashboard.total_snapshots == 0


def test_dashboard_default_values():
    """Verify dashboard returns safe default values on complete failure."""
    service = PortfolioHealthMonitoringDashboardService()
    dashboard = service.build_dashboard()
    assert isinstance(dashboard, PortfolioHealthMonitoringDashboard)
    assert dashboard.monitoring_status in ["UNAVAILABLE", "WAITING", "READY"]

