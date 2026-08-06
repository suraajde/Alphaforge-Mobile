import json
import tempfile
import pytest
from pathlib import Path

from services.portfolio_health_history_service import (
    PortfolioHealthHistoryEntry,
    PortfolioHealthHistoryService,
)
from services.portfolio_health_service import PortfolioHealthResult


@pytest.fixture
def temp_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir) / "portfolio_health_history.json")
        yield path


def test_history_service_instantiation(temp_storage):
    """TEST 1: Verify service instantiation."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    assert service is not None
    assert service.storage_path == temp_storage


def test_save_snapshot(temp_storage):
    """TEST 2: Verify saving snapshot persists entry."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    result = PortfolioHealthResult(
        score=84,
        grade="B",
        diversification_rating="GOOD",
        concentration_rating="MODERATE",
        position_count=12,
        largest_position_weight_pct=15.0,
        cash_allocation_pct=5.0,
    )
    entry = service.save_snapshot(result)

    assert entry is not None
    assert isinstance(entry, PortfolioHealthHistoryEntry)
    assert entry.score == 84
    assert entry.grade == "B"
    assert entry.diversification_rating == "GOOD"
    assert entry.position_count == 12


def test_load_history(temp_storage):
    """TEST 3: Verify load_history returns persisted entries."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    res1 = PortfolioHealthResult(80, "B", "GOOD", "LOW", 10, 10.0, 5.0)
    res2 = PortfolioHealthResult(85, "B", "GOOD", "LOW", 12, 8.0, 5.0)

    service.save_snapshot(res1)
    service.save_snapshot(res2)

    history = service.get_history()
    assert len(history) == 2
    assert history[0].score == 80
    assert history[1].score == 85


def test_get_latest_entry(temp_storage):
    """TEST 4: Verify get_latest returns the most recent entry."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    res1 = PortfolioHealthResult(75, "C", "MODERATE", "MODERATE", 6, 18.0, 12.0)
    res2 = PortfolioHealthResult(90, "A", "GOOD", "LOW", 14, 7.0, 4.0)

    service.save_snapshot(res1)
    service.save_snapshot(res2)

    latest = service.get_latest()
    assert latest is not None
    assert latest.score == 90
    assert latest.grade == "A"


def test_get_previous_entry(temp_storage):
    """TEST 5: Verify get_previous returns second newest entry."""
    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    res1 = PortfolioHealthResult(70, "C", "POOR", "MODERATE", 4, 19.0, 15.0)
    res2 = PortfolioHealthResult(80, "B", "MODERATE", "LOW", 8, 12.0, 8.0)
    res3 = PortfolioHealthResult(90, "A", "GOOD", "LOW", 12, 8.0, 5.0)

    service.save_snapshot(res1)
    service.save_snapshot(res2)
    service.save_snapshot(res3)

    previous = service.get_previous()
    assert previous is not None
    assert previous.score == 80
    assert previous.grade == "B"


def test_missing_file_safety(temp_storage):
    """TEST 6: Verify missing storage file returns empty history safely."""
    missing_path = temp_storage + ".nonexistent"
    service = PortfolioHealthHistoryService(storage_path=missing_path)

    history = service.get_history()
    assert history == []
    assert service.get_latest() is None
    assert service.get_previous() is None


def test_corrupt_file_safety(temp_storage):
    """TEST 7: Verify corrupt storage file returns empty history safely without throwing exceptions."""
    with open(temp_storage, "w", encoding="utf-8") as f:
        f.write("{ INVALID JSON CORRUPTED DATA }")

    service = PortfolioHealthHistoryService(storage_path=temp_storage)
    history = service.get_history()
    assert history == []
    assert service.get_latest() is None
    assert service.get_previous() is None
