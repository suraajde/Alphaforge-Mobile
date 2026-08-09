import json
import shutil
import tempfile
from pathlib import Path
import pytest

from services.portfolio_health_change_detection_service import (
    PortfolioHealthChange,
    PortfolioHealthChangeDetectionService,
    PortfolioHealthChangeReport,
)
from services.portfolio_health_history_service import (
    PortfolioHealthHistoryEntry,
    PortfolioHealthHistoryService,
)


@pytest.fixture
def custom_tmp_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_service_instantiation():
    """Verify service instantiation."""
    service = PortfolioHealthChangeDetectionService()
    assert service is not None


def test_detect_no_history(custom_tmp_dir):
    """Verify change report when history is missing/empty."""
    missing_file = str(custom_tmp_dir / "missing.json")
    hist_svc = PortfolioHealthHistoryService(storage_path=missing_file)
    service = PortfolioHealthChangeDetectionService(history_service=hist_svc)

    report = service.detect_changes()
    assert isinstance(report, PortfolioHealthChangeReport)
    assert report.snapshot_count == 0
    assert report.total_changes == 0
    assert report.has_changes is False
    assert report.changes == []


def test_detect_single_snapshot(custom_tmp_dir):
    """Verify change report when only one snapshot exists."""
    single_file = custom_tmp_dir / "single.json"
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
            "largest_position": "RELIANCE",
        }
    ]
    single_file.write_text(json.dumps(data), encoding="utf-8")

    hist_svc = PortfolioHealthHistoryService(storage_path=str(single_file))
    service = PortfolioHealthChangeDetectionService(history_service=hist_svc)

    report = service.detect_changes()
    assert report.snapshot_count == 1
    assert report.total_changes == 0
    assert report.has_changes is False
    assert report.changes == []


def test_detect_multiple_snapshots(custom_tmp_dir):
    """Verify change report when multiple snapshots exist."""
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
            "timestamp": "2026-08-07T09:15:00Z",
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
    service = PortfolioHealthChangeDetectionService(history_service=hist_svc)

    report = service.detect_changes()
    assert report.snapshot_count == 2
    assert report.has_changes is True
    assert report.total_changes > 0


def test_detect_score_increase():
    """Verify change detection for score increase."""
    service = PortfolioHealthChangeDetectionService()
    prev = PortfolioHealthHistoryEntry("t1", 80, "B", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")
    curr = PortfolioHealthHistoryEntry("t2", 90, "A", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")

    report = service.detect_changes(history=[prev, curr])
    score_change = next(c for c in report.changes if c.field_name == "Health Score")
    assert score_change.change_type == "INCREASED"
    assert score_change.previous_value == "80"
    assert score_change.current_value == "90"


def test_detect_score_decrease():
    """Verify change detection for score decrease."""
    service = PortfolioHealthChangeDetectionService()
    prev = PortfolioHealthHistoryEntry("t1", 90, "A", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")
    curr = PortfolioHealthHistoryEntry("t2", 75, "C", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")

    report = service.detect_changes(history=[prev, curr])
    score_change = next(c for c in report.changes if c.field_name == "Health Score")
    assert score_change.change_type == "DECREASED"
    assert score_change.previous_value == "90"
    assert score_change.current_value == "75"


def test_detect_grade_change():
    """Verify change detection for grade change."""
    service = PortfolioHealthChangeDetectionService()
    prev = PortfolioHealthHistoryEntry("t1", 84, "B", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")
    curr = PortfolioHealthHistoryEntry("t2", 91, "A", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")

    report = service.detect_changes(history=[prev, curr])
    grade_change = next(c for c in report.changes if c.field_name == "Grade")
    assert grade_change.change_type == "CHANGED"
    assert grade_change.previous_value == "B"
    assert grade_change.current_value == "A"


def test_detect_diversification_change():
    """Verify change detection for diversification rating change."""
    service = PortfolioHealthChangeDetectionService()
    prev = PortfolioHealthHistoryEntry("t1", 70, "C", "MODERATE", "LOW", 6, 8.0, 5.0, "RELIANCE")
    curr = PortfolioHealthHistoryEntry("t2", 90, "A", "GOOD", "LOW", 12, 8.0, 5.0, "RELIANCE")

    report = service.detect_changes(history=[prev, curr])
    div_change = next(c for c in report.changes if c.field_name == "Diversification Rating")
    assert div_change.change_type == "CHANGED"
    assert div_change.previous_value == "MODERATE"
    assert div_change.current_value == "GOOD"


def test_detect_concentration_change():
    """Verify change detection for concentration rating change."""
    service = PortfolioHealthChangeDetectionService()
    prev = PortfolioHealthHistoryEntry("t1", 70, "C", "GOOD", "HIGH", 10, 25.0, 5.0, "RELIANCE")
    curr = PortfolioHealthHistoryEntry("t2", 90, "A", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")

    report = service.detect_changes(history=[prev, curr])
    conc_change = next(c for c in report.changes if c.field_name == "Concentration Rating")
    assert conc_change.change_type == "CHANGED"
    assert conc_change.previous_value == "HIGH"
    assert conc_change.current_value == "LOW"


def test_detect_cash_allocation_change():
    """Verify change detection for cash allocation change."""
    service = PortfolioHealthChangeDetectionService()
    prev = PortfolioHealthHistoryEntry("t1", 80, "B", "GOOD", "LOW", 10, 8.0, 8.0, "RELIANCE")
    curr = PortfolioHealthHistoryEntry("t2", 90, "A", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")

    report = service.detect_changes(history=[prev, curr])
    cash_change = next(c for c in report.changes if c.field_name == "Cash Allocation")
    assert cash_change.change_type == "DECREASED"
    assert cash_change.previous_value == "8%"
    assert cash_change.current_value == "5%"


def test_detect_position_count_change():
    """Verify change detection for position count change."""
    service = PortfolioHealthChangeDetectionService()
    prev = PortfolioHealthHistoryEntry("t1", 80, "B", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")
    curr = PortfolioHealthHistoryEntry("t2", 90, "A", "GOOD", "LOW", 12, 8.0, 5.0, "RELIANCE")

    report = service.detect_changes(history=[prev, curr])
    pos_change = next(c for c in report.changes if c.field_name == "Position Count")
    assert pos_change.change_type == "INCREASED"
    assert pos_change.previous_value == "10"
    assert pos_change.current_value == "12"


def test_detect_largest_position_change():
    """Verify change detection for largest position ticker change."""
    service = PortfolioHealthChangeDetectionService()
    prev = PortfolioHealthHistoryEntry("t1", 80, "B", "GOOD", "LOW", 10, 12.0, 5.0, "INFY")
    curr = PortfolioHealthHistoryEntry("t2", 90, "A", "GOOD", "LOW", 10, 8.0, 5.0, "TCS")

    report = service.detect_changes(history=[prev, curr])
    lpos_change = next(c for c in report.changes if c.field_name == "Largest Position")
    assert lpos_change.change_type == "CHANGED"
    assert lpos_change.previous_value == "INFY"
    assert lpos_change.current_value == "TCS"


def test_detect_largest_position_weight_change():
    """Verify change detection for largest position weight percentage change."""
    service = PortfolioHealthChangeDetectionService()
    prev = PortfolioHealthHistoryEntry("t1", 80, "B", "GOOD", "LOW", 10, 15.0, 5.0, "TCS")
    curr = PortfolioHealthHistoryEntry("t2", 90, "A", "GOOD", "LOW", 10, 8.0, 5.0, "TCS")

    report = service.detect_changes(history=[prev, curr])
    lw_change = next(c for c in report.changes if c.field_name == "Largest Position Weight")
    assert lw_change.change_type == "DECREASED"
    assert lw_change.previous_value == "15%"
    assert lw_change.current_value == "8%"


def test_detect_unchanged_values():
    """Verify change detection when both snapshots are identical."""
    service = PortfolioHealthChangeDetectionService()
    prev = PortfolioHealthHistoryEntry("t1", 85, "B", "GOOD", "LOW", 10, 8.0, 5.0, "TCS")
    curr = PortfolioHealthHistoryEntry("t2", 85, "B", "GOOD", "LOW", 10, 8.0, 5.0, "TCS")

    report = service.detect_changes(history=[prev, curr])
    assert report.snapshot_count == 2
    assert report.total_changes == 0
    assert report.has_changes is False
    assert all(c.change_type == "UNCHANGED" for c in report.changes)


def test_corrupt_history_safety(custom_tmp_dir):
    """Verify defensive handling when history contains corrupt JSON."""
    corrupt_file = custom_tmp_dir / "corrupt.json"
    corrupt_file.write_text("INVALID_JSON{", encoding="utf-8")

    hist_svc = PortfolioHealthHistoryService(storage_path=str(corrupt_file))
    service = PortfolioHealthChangeDetectionService(history_service=hist_svc)

    report = service.detect_changes()
    assert report.snapshot_count == 0
    assert report.total_changes == 0
    assert report.has_changes is False
    assert report.changes == []
