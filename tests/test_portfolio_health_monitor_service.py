import json
import shutil
import tempfile
from pathlib import Path
import pytest

from services.portfolio_health_history_service import (
    PortfolioHealthHistoryEntry,
    PortfolioHealthHistoryService,
)
from services.portfolio_health_monitor_service import (
    PortfolioHealthMonitoringState,
    PortfolioHealthMonitorService,
)


@pytest.fixture
def custom_tmp_dir():
    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_service_instantiation():
    """Verify service instantiation."""
    service = PortfolioHealthMonitorService()
    assert service is not None


def test_monitoring_state_exists():
    """Verify get_monitoring_state returns a valid PortfolioHealthMonitoringState."""
    service = PortfolioHealthMonitorService()
    state = service.get_monitoring_state()
    assert state is not None
    assert isinstance(state, PortfolioHealthMonitoringState)


def test_history_unavailable(custom_tmp_dir):
    """Verify state when history file is missing (UNAVAILABLE)."""
    non_existent_file = str(custom_tmp_dir / "non_existent.json")
    history_svc = PortfolioHealthHistoryService(storage_path=non_existent_file)
    service = PortfolioHealthMonitorService(history_service=history_svc)

    state = service.get_monitoring_state()
    assert state.monitoring_enabled is False
    assert state.monitoring_status == "UNAVAILABLE"
    assert state.snapshot_count == 0
    assert state.latest_snapshot_time is None
    assert state.latest_score == 0
    assert state.latest_grade == "-"
    assert service.is_monitoring_ready() is False
    assert service.latest_snapshot_available() is False


def test_history_empty(custom_tmp_dir):
    """Verify state when history file exists but is empty (WAITING)."""
    empty_file = custom_tmp_dir / "empty_history.json"
    empty_file.write_text("[]", encoding="utf-8")

    history_svc = PortfolioHealthHistoryService(storage_path=str(empty_file))
    service = PortfolioHealthMonitorService(history_service=history_svc)

    state = service.get_monitoring_state()
    assert state.monitoring_enabled is True
    assert state.monitoring_status == "WAITING"
    assert state.snapshot_count == 0
    assert state.latest_snapshot_time is None
    assert state.latest_score == 0
    assert state.latest_grade == "-"
    assert service.is_monitoring_ready() is False
    assert service.latest_snapshot_available() is False


def test_corrupt_history(custom_tmp_dir):
    """Verify defensive handling when history file contains corrupt JSON."""
    corrupt_file = custom_tmp_dir / "corrupt_history.json"
    corrupt_file.write_text("NOT_VALID_JSON{", encoding="utf-8")

    history_svc = PortfolioHealthHistoryService(storage_path=str(corrupt_file))
    service = PortfolioHealthMonitorService(history_service=history_svc)

    state = service.get_monitoring_state()
    assert state.monitoring_enabled is False
    assert state.monitoring_status == "UNAVAILABLE"
    assert state.snapshot_count == 0
    assert service.is_monitoring_ready() is False
    assert service.latest_snapshot_available() is False


def test_history_available_ready(custom_tmp_dir):
    """Verify state when valid history entries are available (READY)."""
    valid_file = custom_tmp_dir / "valid_history.json"
    data = [
        {
            "timestamp": "2026-08-07T08:00:00Z",
            "score": 80,
            "grade": "B",
            "diversification_rating": "GOOD",
            "concentration_rating": "LOW",
            "position_count": 10,
            "largest_position_weight_pct": 9.0,
            "cash_allocation_pct": 5.0,
        },
        {
            "timestamp": "2026-08-07T09:15:00Z",
            "score": 91,
            "grade": "A",
            "diversification_rating": "GOOD",
            "concentration_rating": "LOW",
            "position_count": 12,
            "largest_position_weight_pct": 8.0,
            "cash_allocation_pct": 5.0,
        },
    ]
    valid_file.write_text(json.dumps(data), encoding="utf-8")

    history_svc = PortfolioHealthHistoryService(storage_path=str(valid_file))
    service = PortfolioHealthMonitorService(history_service=history_svc)

    state = service.get_monitoring_state()
    assert state.monitoring_enabled is True
    assert state.monitoring_status == "READY"
    assert state.snapshot_count == 2
    assert state.latest_snapshot_time == "2026-08-07T09:15:00Z"
    assert state.latest_score == 91
    assert state.latest_grade == "A"
    assert service.is_monitoring_ready() is True
    assert service.latest_snapshot_available() is True


def test_latest_snapshot_retrieval(custom_tmp_dir):
    """Verify retrieval of latest snapshot timestamp."""
    file_path = custom_tmp_dir / "history.json"
    data = [
        {
            "timestamp": "2026-08-07T09:15:00Z",
            "score": 91,
            "grade": "A",
            "diversification_rating": "GOOD",
            "concentration_rating": "LOW",
            "position_count": 12,
            "largest_position_weight_pct": 8.0,
            "cash_allocation_pct": 5.0,
        }
    ]
    file_path.write_text(json.dumps(data), encoding="utf-8")

    history_svc = PortfolioHealthHistoryService(storage_path=str(file_path))
    service = PortfolioHealthMonitorService(history_service=history_svc)

    state = service.get_monitoring_state()
    assert state.latest_snapshot_time == "2026-08-07T09:15:00Z"


def test_latest_score_retrieval(custom_tmp_dir):
    """Verify retrieval of latest snapshot score."""
    file_path = custom_tmp_dir / "history.json"
    data = [
        {
            "timestamp": "2026-08-07T09:15:00Z",
            "score": 91,
            "grade": "A",
            "diversification_rating": "GOOD",
            "concentration_rating": "LOW",
            "position_count": 12,
            "largest_position_weight_pct": 8.0,
            "cash_allocation_pct": 5.0,
        }
    ]
    file_path.write_text(json.dumps(data), encoding="utf-8")

    history_svc = PortfolioHealthHistoryService(storage_path=str(file_path))
    service = PortfolioHealthMonitorService(history_service=history_svc)

    state = service.get_monitoring_state()
    assert state.latest_score == 91


def test_latest_grade_retrieval(custom_tmp_dir):
    """Verify retrieval of latest snapshot grade."""
    file_path = custom_tmp_dir / "history.json"
    data = [
        {
            "timestamp": "2026-08-07T09:15:00Z",
            "score": 91,
            "grade": "A",
            "diversification_rating": "GOOD",
            "concentration_rating": "LOW",
            "position_count": 12,
            "largest_position_weight_pct": 8.0,
            "cash_allocation_pct": 5.0,
        }
    ]
    file_path.write_text(json.dumps(data), encoding="utf-8")

    history_svc = PortfolioHealthHistoryService(storage_path=str(file_path))
    service = PortfolioHealthMonitorService(history_service=history_svc)

    state = service.get_monitoring_state()
    assert state.latest_grade == "A"
