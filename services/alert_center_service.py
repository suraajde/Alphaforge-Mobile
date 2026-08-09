"""Alert Center Service (Sprint 15.0.0)

Provides persistence, state calculation, and retrieval for portfolio alerts.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class PortfolioAlert:
    alert_id: str
    timestamp: str
    alert_type: str
    severity: str
    title: str
    description: str
    status: str


@dataclass
class AlertCenterState:
    total_alerts: int
    active_alerts: int
    acknowledged_alerts: int
    dismissed_alerts: int
    alerts: list[PortfolioAlert]


from config.path_config import get_data_path


class AlertCenterService:
    """Service layer for persisting and querying portfolio alerts safely."""

    def __init__(self, storage_path: Optional[str] = None) -> None:
        if storage_path is not None:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = get_data_path("alerts/portfolio_alerts.json")

    def _ensure_storage_exists(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.storage_path.exists():
                self.storage_path.write_text("[]", encoding="utf-8")
        except Exception:
            pass

    def load_alerts(self) -> list[PortfolioAlert]:
        """Loads and returns all PortfolioAlert entries from JSON storage safely."""
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

            alerts: list[PortfolioAlert] = []
            for item in raw_list:
                if isinstance(item, dict):
                    alerts.append(
                        PortfolioAlert(
                            alert_id=str(item.get("alert_id", "")),
                            timestamp=str(item.get("timestamp", "")),
                            alert_type=str(item.get("alert_type", "")),
                            severity=str(item.get("severity", "INFO")),
                            title=str(item.get("title", "")),
                            description=str(item.get("description", "")),
                            status=str(item.get("status", "ACTIVE")),
                        )
                    )
            return alerts
        except Exception:
            return []

    def save_alerts(self, alerts: list[PortfolioAlert]) -> None:
        """Saves a list of PortfolioAlert entries to JSON storage safely."""
        try:
            self._ensure_storage_exists()
            raw_list = [asdict(a) for a in alerts]
            temp_path = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
            temp_path.write_text(json.dumps(raw_list, indent=2), encoding="utf-8")
            temp_path.replace(self.storage_path)
        except Exception:
            pass

    def get_state(self) -> AlertCenterState:
        """Calculates and returns the current AlertCenterState safely."""
        default_state = AlertCenterState(
            total_alerts=0,
            active_alerts=0,
            acknowledged_alerts=0,
            dismissed_alerts=0,
            alerts=[],
        )

        try:
            alerts = self.load_alerts()
            total_alerts = len(alerts)
            active_alerts = sum(1 for a in alerts if a.status == "ACTIVE")
            acknowledged_alerts = sum(1 for a in alerts if a.status == "ACKNOWLEDGED")
            dismissed_alerts = sum(1 for a in alerts if a.status == "DISMISSED")

            return AlertCenterState(
                total_alerts=total_alerts,
                active_alerts=active_alerts,
                acknowledged_alerts=acknowledged_alerts,
                dismissed_alerts=dismissed_alerts,
                alerts=alerts,
            )
        except Exception:
            return default_state

    def get_active_alerts(self) -> list[PortfolioAlert]:
        """Returns all alerts with status == 'ACTIVE' safely."""
        try:
            return [a for a in self.load_alerts() if a.status == "ACTIVE"]
        except Exception:
            return []
