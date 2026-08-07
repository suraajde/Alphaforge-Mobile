"""Alert History Service (Sprint 15.0.4)

Provides persistent historical tracking and retrieval of portfolio alerts.

This service is HISTORY MANAGEMENT ONLY.
It does NOT generate alerts, modify alerts, send notifications, or recommend investment actions.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class AlertHistoryEntry:
    """Represents a single historical alert entry."""
    alert_id: str
    timestamp: str
    alert_type: str
    severity: str
    title: str
    description: str
    status: str


@dataclass
class AlertHistory:
    """Aggregated historical summary of portfolio alerts."""
    total_entries: int
    latest_timestamp: Optional[str]
    earliest_timestamp: Optional[str]
    entries: list[AlertHistoryEntry]


class AlertHistoryService:
    """Service layer for persisting, appending, and querying alert history safely."""

    def __init__(self, storage_path: Optional[str] = None) -> None:
        if storage_path is not None:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path("data/alerts/alert_history.json")

    def _ensure_storage_exists(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.storage_path.exists():
                self.storage_path.write_text("[]", encoding="utf-8")
        except Exception:
            pass

    def load_history(self) -> list[AlertHistoryEntry]:
        """Loads and returns all AlertHistoryEntry objects from JSON storage safely."""
        try:
            if not self.storage_path.exists():
                self._ensure_storage_exists()
                return []

            content = self.storage_path.read_text(encoding="utf-8").strip()
            if not content:
                return []

            raw_list = json.loads(content)
            if not isinstance(raw_list, list):
                return []

            entries: list[AlertHistoryEntry] = []
            for item in raw_list:
                if isinstance(item, dict):
                    entries.append(
                        AlertHistoryEntry(
                            alert_id=str(item.get("alert_id", "")),
                            timestamp=str(item.get("timestamp", "")),
                            alert_type=str(item.get("alert_type", "")),
                            severity=str(item.get("severity", "INFO")),
                            title=str(item.get("title", "")),
                            description=str(item.get("description", "")),
                            status=str(item.get("status", "ACTIVE")),
                        )
                    )
            return entries
        except Exception:
            return []

    def save_history(self, entries: Optional[list[Any]] = None) -> None:
        """Appends new alert entries to historical storage and saves safely."""
        try:
            if entries is None:
                return

            self._ensure_storage_exists()
            existing_entries = self.load_history()
            seen_ids = {e.alert_id for e in existing_entries if e.alert_id}

            updated = False
            for item in entries:
                entry = self._to_entry(item)
                if entry is not None:
                    if not entry.alert_id or entry.alert_id not in seen_ids:
                        if entry.alert_id:
                            seen_ids.add(entry.alert_id)
                        existing_entries.append(entry)
                        updated = True

            if updated or not self.storage_path.exists():
                raw_list = [asdict(e) for e in existing_entries]
                self.storage_path.write_text(json.dumps(raw_list, indent=2), encoding="utf-8")
        except Exception:
            pass

    def get_history(self) -> AlertHistory:
        """Calculates and returns the AlertHistory object safely."""
        default_history = AlertHistory(
            total_entries=0,
            latest_timestamp=None,
            earliest_timestamp=None,
            entries=[],
        )

        try:
            entries = self.load_history()
            if not entries:
                return default_history

            total = len(entries)
            earliest_ts = entries[0].timestamp if entries[0].timestamp else None
            latest_ts = entries[-1].timestamp if entries[-1].timestamp else None

            return AlertHistory(
                total_entries=total,
                latest_timestamp=latest_ts,
                earliest_timestamp=earliest_ts,
                entries=entries,
            )
        except Exception:
            return default_history

    def get_latest(self) -> Optional[AlertHistoryEntry]:
        """Returns the most recent AlertHistoryEntry safely, or None."""
        try:
            entries = self.load_history()
            if entries:
                return entries[-1]
            return None
        except Exception:
            return None

    def get_previous(self) -> Optional[AlertHistoryEntry]:
        """Returns the second most recent AlertHistoryEntry safely, or None."""
        try:
            entries = self.load_history()
            if len(entries) >= 2:
                return entries[-2]
            return None
        except Exception:
            return None

    def _to_entry(self, item: Any) -> Optional[AlertHistoryEntry]:
        """Helper to convert dict, PortfolioAlert, or AlertHistoryEntry into AlertHistoryEntry."""
        try:
            if isinstance(item, AlertHistoryEntry):
                return item

            if hasattr(item, "alert_id") and hasattr(item, "timestamp"):
                return AlertHistoryEntry(
                    alert_id=str(getattr(item, "alert_id", "")),
                    timestamp=str(getattr(item, "timestamp", "")),
                    alert_type=str(getattr(item, "alert_type", "")),
                    severity=str(getattr(item, "severity", "INFO")),
                    title=str(getattr(item, "title", "")),
                    description=str(getattr(item, "description", "")),
                    status=str(getattr(item, "status", "ACTIVE")),
                )

            if isinstance(item, dict):
                return AlertHistoryEntry(
                    alert_id=str(item.get("alert_id", "")),
                    timestamp=str(item.get("timestamp", "")),
                    alert_type=str(item.get("alert_type", "")),
                    severity=str(item.get("severity", "INFO")),
                    title=str(item.get("title", "")),
                    description=str(item.get("description", "")),
                    status=str(item.get("status", "ACTIVE")),
                )
            return None
        except Exception:
            return None
