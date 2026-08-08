"""Unit test suite for History Service JSON caching (Sprint 14.0.1)."""

import json
import os
import tempfile
import pytest
from services.portfolio_health_history_service import PortfolioHealthHistoryService


def test_first_load_reads_file():
    """Verify first load reads entries from storage file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "history.json")
        data = [
            {
                "timestamp": "2026-08-08T12:00:00Z",
                "score": 85,
                "grade": "B",
                "diversification_rating": "GOOD",
                "concentration_rating": "LOW",
                "position_count": 10,
                "largest_position_weight_pct": 8.0,
                "cash_allocation_pct": 5.0,
                "largest_position": "AAPL",
            }
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        svc = PortfolioHealthHistoryService(storage_path=path)
        history = svc.get_history()

        assert len(history) == 1
        assert history[0].score == 85
        assert history[0].largest_position == "AAPL"


def test_unchanged_file_uses_cache():
    """Verify second call on unchanged file uses cached entries."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "history.json")
        data = [{"timestamp": "2026-08-08T12:00:00Z", "score": 90, "grade": "A"}]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        svc = PortfolioHealthHistoryService(storage_path=path)
        h1 = svc.get_history()
        h2 = svc.get_history()

        assert h1 == h2
        assert h1 is not h2  # Shallow copy ensures list mutation safety


def test_caller_list_mutation_does_not_corrupt_cache():
    """Verify mutating returned history list does not corrupt cached internal state."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "history.json")
        data = [{"timestamp": "2026-08-08T12:00:00Z", "score": 90, "grade": "A"}]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        svc = PortfolioHealthHistoryService(storage_path=path)
        h1 = svc.get_history()
        h1.clear()  # Caller clears their local list

        h2 = svc.get_history()
        assert len(h2) == 1  # Cached history inside service remains intact!


def test_modified_file_reloads_from_disk():
    """Verify modifying file timestamp or content reloads fresh history."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "history.json")
        data1 = [{"timestamp": "2026-08-08T12:00:00Z", "score": 80, "grade": "B"}]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data1, f)

        svc = PortfolioHealthHistoryService(storage_path=path)
        h1 = svc.get_history()
        assert len(h1) == 1

        # Update file with new snapshot and new mtime
        data2 = [
            {"timestamp": "2026-08-08T12:00:00Z", "score": 80, "grade": "B"},
            {"timestamp": "2026-08-08T13:00:00Z", "score": 95, "grade": "A"},
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data2, f)

        # Explicitly advance mtime if filesystem timer resolution is coarse
        stat = os.stat(path)
        os.utime(path, (stat.st_atime, stat.st_mtime + 5.0))

        h2 = svc.get_history()
        assert len(h2) == 2
        assert h2[-1].score == 95


def test_missing_file_handled_safely():
    """Verify missing history storage file is handled safely."""
    svc = PortfolioHealthHistoryService(storage_path="D:/ALPHAFORGE/non_existent_history.json")
    history = svc.get_history()
    assert history == []


def test_corrupt_file_handled_safely():
    """Verify corrupt JSON file is handled safely without raising uncaught exceptions."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "corrupt.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON DATA }}}")

        svc = PortfolioHealthHistoryService(storage_path=path)
        history = svc.get_history()
        assert isinstance(history, list)
