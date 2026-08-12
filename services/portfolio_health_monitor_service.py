"""Portfolio Health Monitor Service (Sprint 13.4.0)

Provides the monitoring layer on top of PortfolioHealthHistoryService to report portfolio health state.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from services.portfolio_health_history_service import PortfolioHealthHistoryService


@dataclass
class PortfolioHealthMonitoringState:
    monitoring_enabled: bool
    monitoring_status: str
    snapshot_count: int
    latest_snapshot_time: Optional[str]
    latest_score: int
    latest_grade: str


class PortfolioHealthMonitorService:
    """Service for checking portfolio health monitoring state and readiness."""

    def __init__(self, history_service: Optional[PortfolioHealthHistoryService] = None) -> None:
        self.history_service = history_service if history_service is not None else PortfolioHealthHistoryService()

    def get_monitoring_state(self) -> PortfolioHealthMonitoringState:
        """Evaluates and returns the current portfolio health monitoring state safely without raising exceptions."""
        default_state = PortfolioHealthMonitoringState(
            monitoring_enabled=False,
            monitoring_status="UNAVAILABLE",
            snapshot_count=0,
            latest_snapshot_time=None,
            latest_score=0,
            latest_grade="-",
        )

        try:
            if self.history_service is None:
                return default_state

            storage_path = getattr(self.history_service, "storage_path", None)
            if storage_path is None or not os.path.exists(storage_path):
                try:
                    from services.portfolio_state_service import PortfolioStateService
                    st_svc = PortfolioStateService()
                    st = st_svc.load_state()
                    if isinstance(st, dict):
                        pos = st.get("positions") or (st.get("state", {}).get("positions") if isinstance(st.get("state"), dict) else None)
                        if pos and isinstance(pos, dict) and len(pos) >= 1:
                            from services.portfolio_health_service import PortfolioHealthService
                            ph_svc = PortfolioHealthService(history_service=self.history_service)
                            ph_svc.evaluate()
                except Exception:
                    pass

            if storage_path is None or not os.path.exists(storage_path):
                return default_state

            # Verify file read safety (e.g. corrupt JSON or unreadable file)
            try:
                with open(storage_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        # Empty file exists on disk -> WAITING
                        return PortfolioHealthMonitoringState(
                            monitoring_enabled=True,
                            monitoring_status="WAITING",
                            snapshot_count=0,
                            latest_snapshot_time=None,
                            latest_score=0,
                            latest_grade="-",
                        )
                    data = json.loads(content)
                    if not isinstance(data, list):
                        return default_state
            except Exception:
                # File is corrupt or invalid JSON -> UNAVAILABLE
                return default_state

            history = self.history_service.get_history()

            if not history:
                try:
                    from services.portfolio_state_service import PortfolioStateService
                    st_svc = PortfolioStateService()
                    st = st_svc.load_state()
                    if isinstance(st, dict):
                        pos = st.get("positions") or (st.get("state", {}).get("positions") if isinstance(st.get("state"), dict) else None)
                        if pos and isinstance(pos, dict) and len(pos) >= 1:
                            from services.portfolio_health_service import PortfolioHealthService
                            ph_svc = PortfolioHealthService(history_service=self.history_service)
                            ph_svc.evaluate()
                            history = self.history_service.get_history()
                except Exception:
                    pass

            if not history:
                return PortfolioHealthMonitoringState(
                    monitoring_enabled=True,
                    monitoring_status="WAITING",
                    snapshot_count=0,
                    latest_snapshot_time=None,
                    latest_score=0,
                    latest_grade="-",
                )

            latest = history[-1]
            return PortfolioHealthMonitoringState(
                monitoring_enabled=True,
                monitoring_status="READY",
                snapshot_count=len(history),
                latest_snapshot_time=getattr(latest, "timestamp", None),
                latest_score=getattr(latest, "score", 0),
                latest_grade=getattr(latest, "grade", "-"),
            )
        except Exception:
            return default_state

    def is_monitoring_ready(self) -> bool:
        """Returns True if monitoring status is READY."""
        try:
            state = self.get_monitoring_state()
            return state.monitoring_status == "READY"
        except Exception:
            return False

    def latest_snapshot_available(self) -> bool:
        """Returns True if at least one snapshot is stored and its timestamp is available."""
        try:
            state = self.get_monitoring_state()
            return state.latest_snapshot_time is not None and state.snapshot_count > 0
        except Exception:
            return False
