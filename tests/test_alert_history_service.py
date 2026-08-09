import shutil
import tempfile
from pathlib import Path
import pytest

from services.alert_history_service import (
    AlertHistory,
    AlertHistoryEntry,
    AlertHistoryService,
)


def test_service_instantiation():
    """Verify AlertHistoryService instantiation."""
    service = AlertHistoryService()
    assert service is not None


def test_empty_history():
    """Verify get_history returns empty AlertHistory when no file exists."""
    temp_dir = tempfile.mkdtemp()
    try:
        empty_file = Path(temp_dir) / "empty_history.json"
        service = AlertHistoryService(storage_path=str(empty_file))
        history = service.get_history()

        assert isinstance(history, AlertHistory)
        assert history.total_entries == 0
        assert history.latest_timestamp is None
        assert history.earliest_timestamp is None
        assert history.entries == []
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_save_and_load_history():
    """Verify save_history and load_history roundtrip."""
    temp_dir = tempfile.mkdtemp()
    try:
        history_file = Path(temp_dir) / "history.json"
        service = AlertHistoryService(storage_path=str(history_file))

        entries = [
            AlertHistoryEntry("1", "2026-08-07 10:00", "TYPE1", "INFO", "Title 1", "Desc 1", "ACTIVE"),
            AlertHistoryEntry("2", "2026-08-07 10:05", "TYPE2", "HIGH", "Title 2", "Desc 2", "ACTIVE"),
        ]

        service.save_history(entries)
        loaded = service.load_history()

        assert len(loaded) == 2
        assert loaded[0].alert_id == "1"
        assert loaded[0].severity == "INFO"
        assert loaded[1].alert_id == "2"
        assert loaded[1].severity == "HIGH"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_missing_history_file():
    """Verify graceful handling when history file is missing."""
    temp_dir = tempfile.mkdtemp()
    try:
        missing_file = Path(temp_dir) / "nonexistent.json"
        service = AlertHistoryService(storage_path=str(missing_file))

        history = service.get_history()
        assert history.total_entries == 0
        assert history.entries == []
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_corrupt_history_file():
    """Verify graceful handling when history file is corrupt JSON."""
    temp_dir = tempfile.mkdtemp()
    try:
        corrupt_file = Path(temp_dir) / "corrupt.json"
        corrupt_file.write_text("{invalid json", encoding="utf-8")

        service = AlertHistoryService(storage_path=str(corrupt_file))
        history = service.get_history()

        assert isinstance(history, AlertHistory)
        assert history.total_entries == 0
        assert history.entries == []
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_latest_entry():
    """Verify get_latest returns the most recent entry."""
    temp_dir = tempfile.mkdtemp()
    try:
        history_file = Path(temp_dir) / "history.json"
        service = AlertHistoryService(storage_path=str(history_file))

        entries = [
            AlertHistoryEntry("1", "2026-08-07 10:00", "TYPE1", "INFO", "First", "D1", "ACTIVE"),
            AlertHistoryEntry("2", "2026-08-07 10:10", "TYPE2", "MEDIUM", "Second", "D2", "ACTIVE"),
            AlertHistoryEntry("3", "2026-08-07 10:20", "TYPE3", "CRITICAL", "Latest", "D3", "ACTIVE"),
        ]
        service.save_history(entries)

        latest = service.get_latest()
        assert latest is not None
        assert latest.alert_id == "3"
        assert latest.title == "Latest"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_previous_entry():
    """Verify get_previous returns the second most recent entry."""
    temp_dir = tempfile.mkdtemp()
    try:
        history_file = Path(temp_dir) / "history.json"
        service = AlertHistoryService(storage_path=str(history_file))

        entries = [
            AlertHistoryEntry("1", "2026-08-07 10:00", "TYPE1", "INFO", "First", "D1", "ACTIVE"),
            AlertHistoryEntry("2", "2026-08-07 10:10", "TYPE2", "MEDIUM", "Previous", "D2", "ACTIVE"),
            AlertHistoryEntry("3", "2026-08-07 10:20", "TYPE3", "CRITICAL", "Latest", "D3", "ACTIVE"),
        ]
        service.save_history(entries)

        previous = service.get_previous()
        assert previous is not None
        assert previous.alert_id == "2"
        assert previous.title == "Previous"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_chronological_ordering():
    """Verify chronological ordering and earliest/latest timestamp calculation."""
    temp_dir = tempfile.mkdtemp()
    try:
        history_file = Path(temp_dir) / "history.json"
        service = AlertHistoryService(storage_path=str(history_file))

        entries = [
            AlertHistoryEntry("1", "2026-08-01 09:00", "TYPE1", "LOW", "Earliest Alert", "D1", "ACTIVE"),
            AlertHistoryEntry("2", "2026-08-05 12:00", "TYPE2", "MEDIUM", "Mid Alert", "D2", "ACTIVE"),
            AlertHistoryEntry("3", "2026-08-07 18:00", "TYPE3", "HIGH", "Latest Alert", "D3", "ACTIVE"),
        ]
        service.save_history(entries)

        history = service.get_history()
        assert history.total_entries == 3
        assert history.earliest_timestamp == "2026-08-01 09:00"
        assert history.latest_timestamp == "2026-08-07 18:00"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_defensive_exception_handling():
    """Verify defensive exception handling on corrupted state or broken storage."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Invalid directory path as file to force OS error
        invalid_path = Path(temp_dir) / "dir_as_file"
        invalid_path.mkdir()

        service = AlertHistoryService(storage_path=str(invalid_path))
        history = service.get_history()

        assert isinstance(history, AlertHistory)
        assert history.total_entries == 0
        assert history.entries == []
        assert service.get_latest() is None
        assert service.get_previous() is None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
