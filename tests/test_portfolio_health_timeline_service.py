import json
import shutil
import tempfile
from pathlib import Path
import pytest

from services.portfolio_health_history_service import (
    PortfolioHealthHistoryEntry,
    PortfolioHealthHistoryService,
)
from services.portfolio_health_timeline_service import (
    PortfolioHealthTimeline,
    PortfolioHealthTimelineEntry,
    PortfolioHealthTimelineService,
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
    service = PortfolioHealthTimelineService()
    assert service is not None


def test_timeline_exists():
    """Verify build_timeline returns a valid PortfolioHealthTimeline object."""
    service = PortfolioHealthTimelineService()
    timeline = service.build_timeline()
    assert timeline is not None
    assert isinstance(timeline, PortfolioHealthTimeline)


def test_missing_history(custom_tmp_dir):
    """Verify timeline safety when history file is missing."""
    missing_file = str(custom_tmp_dir / "missing.json")
    hist_svc = PortfolioHealthHistoryService(storage_path=missing_file)
    service = PortfolioHealthTimelineService(history_service=hist_svc)

    timeline = service.build_timeline()
    assert timeline.total_entries == 0
    assert timeline.latest_timestamp is None
    assert timeline.earliest_timestamp is None
    assert timeline.entries == []


def test_empty_history(custom_tmp_dir):
    """Verify timeline safety when history file is empty."""
    empty_file = custom_tmp_dir / "empty.json"
    empty_file.write_text("[]", encoding="utf-8")

    hist_svc = PortfolioHealthHistoryService(storage_path=str(empty_file))
    service = PortfolioHealthTimelineService(history_service=hist_svc)

    timeline = service.build_timeline()
    assert timeline.total_entries == 0
    assert timeline.latest_timestamp is None
    assert timeline.earliest_timestamp is None
    assert timeline.entries == []


def test_single_snapshot(custom_tmp_dir):
    """Verify timeline building with a single snapshot."""
    file_path = custom_tmp_dir / "single.json"
    data = [
        {
            "timestamp": "2026-07-01T10:00:00Z",
            "score": 80,
            "grade": "B",
            "diversification_rating": "GOOD",
            "concentration_rating": "LOW",
            "position_count": 10,
            "largest_position_weight_pct": 8.0,
            "cash_allocation_pct": 5.0,
            "largest_position": "RELIANCE",
        }
    ]
    file_path.write_text(json.dumps(data), encoding="utf-8")

    hist_svc = PortfolioHealthHistoryService(storage_path=str(file_path))
    service = PortfolioHealthTimelineService(history_service=hist_svc)

    timeline = service.build_timeline()
    assert timeline.total_entries == 1
    assert timeline.earliest_timestamp == "2026-07-01T10:00:00Z"
    assert timeline.latest_timestamp == "2026-07-01T10:00:00Z"
    assert len(timeline.entries) == 1

    entry = timeline.entries[0]
    assert entry.sequence == 1
    assert entry.score == 80
    assert entry.grade == "B"
    assert entry.trend_direction == "STABLE"
    assert entry.change_count == 0


def test_multiple_snapshots_and_chronological_ordering():
    """Verify timeline orders entries chronologically (Oldest -> Newest)."""
    service = PortfolioHealthTimelineService()
    e1 = PortfolioHealthHistoryEntry("2026-07-01T10:00:00Z", 80, "B", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")
    e2 = PortfolioHealthHistoryEntry("2026-07-15T10:00:00Z", 84, "B", "GOOD", "LOW", 12, 8.0, 5.0, "RELIANCE")
    e3 = PortfolioHealthHistoryEntry("2026-08-08T10:00:00Z", 91, "A", "GOOD", "LOW", 12, 8.0, 5.0, "RELIANCE")

    # Pass in reverse order to test sorting
    timeline = service.build_timeline(history=[e3, e1, e2])

    assert timeline.total_entries == 3
    assert timeline.earliest_timestamp == "2026-07-01T10:00:00Z"
    assert timeline.latest_timestamp == "2026-08-08T10:00:00Z"

    assert timeline.entries[0].sequence == 1
    assert timeline.entries[0].timestamp == "2026-07-01T10:00:00Z"
    assert timeline.entries[1].sequence == 2
    assert timeline.entries[1].timestamp == "2026-07-15T10:00:00Z"
    assert timeline.entries[2].sequence == 3
    assert timeline.entries[2].timestamp == "2026-08-08T10:00:00Z"


def test_latest_and_earliest_timestamp():
    """Verify latest and earliest timestamp calculations."""
    service = PortfolioHealthTimelineService()
    e1 = PortfolioHealthHistoryEntry("2026-07-01T10:00:00Z", 80, "B", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")
    e2 = PortfolioHealthHistoryEntry("2026-08-08T10:00:00Z", 91, "A", "GOOD", "LOW", 12, 8.0, 5.0, "RELIANCE")

    timeline = service.build_timeline(history=[e1, e2])
    assert timeline.earliest_timestamp == "2026-07-01T10:00:00Z"
    assert timeline.latest_timestamp == "2026-08-08T10:00:00Z"


def test_trend_values_in_timeline():
    """Verify trend direction values across timeline entries."""
    service = PortfolioHealthTimelineService()
    e1 = PortfolioHealthHistoryEntry("t1", 80, "B", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")
    e2 = PortfolioHealthHistoryEntry("t2", 84, "B", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")
    e3 = PortfolioHealthHistoryEntry("t3", 75, "C", "GOOD", "LOW", 10, 8.0, 5.0, "RELIANCE")

    timeline = service.build_timeline(history=[e1, e2, e3])
    assert timeline.entries[0].trend_direction == "STABLE"
    assert timeline.entries[1].trend_direction == "IMPROVING"
    assert timeline.entries[2].trend_direction == "DETERIORATING"


def test_change_counts_in_timeline():
    """Verify change count logic across timeline entries."""
    service = PortfolioHealthTimelineService()
    e1 = PortfolioHealthHistoryEntry("t1", 80, "B", "GOOD", "MODERATE", 10, 15.0, 8.0, "INFY")
    e2 = PortfolioHealthHistoryEntry("t2", 91, "A", "GOOD", "LOW", 12, 8.0, 5.0, "TCS")

    timeline = service.build_timeline(history=[e1, e2])
    assert timeline.entries[0].change_count == 0
    assert timeline.entries[1].change_count > 0


def test_corrupt_history_safety(custom_tmp_dir):
    """Verify defensive handling when history file is corrupt."""
    corrupt_file = custom_tmp_dir / "corrupt.json"
    corrupt_file.write_text("INVALID_JSON{", encoding="utf-8")

    hist_svc = PortfolioHealthHistoryService(storage_path=str(corrupt_file))
    service = PortfolioHealthTimelineService(history_service=hist_svc)

    timeline = service.build_timeline()
    assert timeline.total_entries == 0
    assert timeline.latest_timestamp is None
    assert timeline.earliest_timestamp is None
    assert timeline.entries == []
