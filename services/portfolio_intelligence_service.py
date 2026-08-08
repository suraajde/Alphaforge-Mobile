"""Portfolio Intelligence Foundation Service (Sprint 13.8.0)

Provides foundational data models, summary generation, snapshot creation, and persistent
history tracking for the Portfolio Intelligence Layer (Chapter 18).

IMPORTANT SCOPE BOUNDARY:
This service ONLY collects, normalizes, summarizes, displays, and persists factual
portfolio intelligence information.
It does NOT perform fund/ETF quality scoring, SIP optimization, opportunity scoring,
risk scoring, predictive intelligence, Alpha 12 selection, challenger evaluation,
buy/sell/hold recommendations, trade execution, or broker integration.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from typing import Any, Optional


@dataclass
class PortfolioIntelligenceSnapshot:
    """Factual snapshot representing portfolio state at a given timestamp."""

    timestamp: str
    total_value: float
    total_holdings: int
    account_count: int
    intelligence_status: str  # e.g., "HEALTHY", "MONITOR", "UNAVAILABLE", "EMPTY"


@dataclass
class PortfolioIntelligenceSummary:
    """Summary metrics container for portfolio intelligence."""

    intelligence_status: str
    total_value: float
    total_holdings: int
    account_count: int
    latest_timestamp: Optional[str] = None


@dataclass
class PortfolioIntelligenceResult:
    """Complete portfolio intelligence result container."""

    summary: PortfolioIntelligenceSummary
    snapshots: list[PortfolioIntelligenceSnapshot] = field(default_factory=list)


def _empty_summary(status: str = "EMPTY") -> PortfolioIntelligenceSummary:
    """Return a safe empty PortfolioIntelligenceSummary."""
    return PortfolioIntelligenceSummary(
        intelligence_status=status,
        total_value=0.0,
        total_holdings=0,
        account_count=0,
        latest_timestamp=None,
    )


def _empty_result(status: str = "EMPTY") -> PortfolioIntelligenceResult:
    """Return a safe empty PortfolioIntelligenceResult."""
    return PortfolioIntelligenceResult(
        summary=_empty_summary(status=status),
        snapshots=[],
    )


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


class PortfolioIntelligenceService:
    """Foundational service for the Portfolio Intelligence Layer.

    Collects, normalizes, summarizes, and persists factual portfolio state snapshots.
    Operates defensively without side effects on portfolio holdings or execution state.
    """

    _DEFAULT_STORAGE = os.path.join("data", "intelligence", "portfolio_intelligence_history.json")

    def __init__(
        self,
        portfolio_service: Optional[Any] = None,
        history_path: Optional[str] = None,
    ) -> None:
        """Initialize PortfolioIntelligenceService with optional dependencies."""
        self._portfolio_service = portfolio_service
        self._history_path = (
            history_path if history_path is not None else self._DEFAULT_STORAGE
        )

    def _get_portfolio_service(self) -> Optional[Any]:
        """Safely retrieve or instantiate the application portfolio service."""
        if self._portfolio_service is not None:
            return self._portfolio_service
        try:
            from services.portfolio_application_service import (
                PortfolioApplicationService,
            )

            return PortfolioApplicationService()
        except Exception:
            return None

    def load_portfolio(self, portfolio_data: Optional[Any] = None) -> PortfolioIntelligenceSnapshot:
        """Extract a factual PortfolioIntelligenceSnapshot from portfolio input."""
        try:
            if portfolio_data is None:
                ps = self._get_portfolio_service()
                if ps is not None:
                    if hasattr(ps, "get_portfolio_summary"):
                        portfolio_data = ps.get_portfolio_summary()
                    elif hasattr(ps, "get_rebalancing_state"):
                        portfolio_data = ps.get_rebalancing_state()

            if portfolio_data is None:
                return PortfolioIntelligenceSnapshot(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    total_value=0.0,
                    total_holdings=0,
                    account_count=0,
                    intelligence_status="UNAVAILABLE",
                )

            # Dictionary access or attribute access
            if isinstance(portfolio_data, dict):
                tot_val = _safe_float(
                    portfolio_data.get("portfolio_value", portfolio_data.get("total_value", 0.0))
                )
                pos_cnt = _safe_int(
                    portfolio_data.get("position_count", portfolio_data.get("total_positions", len(portfolio_data.get("positions", []))))
                )
                acct_cnt = _safe_int(
                    portfolio_data.get("account_count", 1 if pos_cnt > 0 else 0)
                )
                status_str = str(portfolio_data.get("status", "HEALTHY")).upper()
            else:
                tot_val = _safe_float(
                    getattr(portfolio_data, "total_value", getattr(portfolio_data, "portfolio_value", 0.0))
                )
                pos_cnt = _safe_int(
                    getattr(portfolio_data, "total_positions", getattr(portfolio_data, "position_count", len(getattr(portfolio_data, "positions", []))))
                )
                acct_cnt = _safe_int(
                    getattr(portfolio_data, "account_count", 1 if pos_cnt > 0 else 0)
                )
                status_str = str(getattr(portfolio_data, "status", "HEALTHY")).upper()

            if status_str not in ("HEALTHY", "MONITOR", "UNAVAILABLE", "EMPTY", "OK"):
                status_str = "HEALTHY" if pos_cnt > 0 else "EMPTY"
            elif status_str == "OK":
                status_str = "HEALTHY" if pos_cnt > 0 else "EMPTY"

            ts = datetime.now(timezone.utc).isoformat()

            return PortfolioIntelligenceSnapshot(
                timestamp=ts,
                total_value=round(tot_val, 2),
                total_holdings=pos_cnt,
                account_count=acct_cnt,
                intelligence_status=status_str if pos_cnt > 0 else "EMPTY",
            )
        except Exception:
            return PortfolioIntelligenceSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_value=0.0,
                total_holdings=0,
                account_count=0,
                intelligence_status="UNAVAILABLE",
            )

    def build_summary(
        self, snapshot: Optional[PortfolioIntelligenceSnapshot] = None
    ) -> PortfolioIntelligenceSummary:
        """Build summary metrics from a single snapshot."""
        try:
            if snapshot is None:
                return _empty_summary("EMPTY")

            return PortfolioIntelligenceSummary(
                intelligence_status=snapshot.intelligence_status,
                total_value=snapshot.total_value,
                total_holdings=snapshot.total_holdings,
                account_count=snapshot.account_count,
                latest_timestamp=snapshot.timestamp,
            )
        except Exception:
            return _empty_summary("UNAVAILABLE")

    def load_history(self) -> list[PortfolioIntelligenceSnapshot]:
        """Load persistent history from disk safely."""
        try:
            if not os.path.exists(self._history_path):
                return []

            with open(self._history_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            if not isinstance(data, dict):
                return []

            raw_snapshots = data.get("snapshots", [])
            if not isinstance(raw_snapshots, list):
                return []

            snapshots: list[PortfolioIntelligenceSnapshot] = []
            for item in raw_snapshots:
                if not isinstance(item, dict):
                    continue
                try:
                    ts = str(item.get("timestamp", ""))
                    if not ts:
                        continue
                    snap = PortfolioIntelligenceSnapshot(
                        timestamp=ts,
                        total_value=_safe_float(item.get("total_value", 0.0)),
                        total_holdings=_safe_int(item.get("total_holdings", 0)),
                        account_count=_safe_int(item.get("account_count", 0)),
                        intelligence_status=str(item.get("intelligence_status", "HEALTHY")),
                    )
                    snapshots.append(snap)
                except Exception:
                    continue

            snapshots.sort(key=lambda s: s.timestamp)
            return snapshots
        except Exception:
            return []

    def save_history(self, snapshots: list[PortfolioIntelligenceSnapshot]) -> None:
        """Save history snapshots to disk safely."""
        try:
            dir_name = os.path.dirname(self._history_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            valid_snaps = [
                asdict(s)
                for s in snapshots
                if isinstance(s, PortfolioIntelligenceSnapshot)
            ]
            valid_snaps.sort(key=lambda item: item.get("timestamp", ""))

            data = {
                "total_snapshots": len(valid_snaps),
                "snapshots": valid_snaps,
            }

            temp_path = self._history_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
            os.replace(temp_path, self._history_path)
        except Exception:
            pass

    def record_snapshot(
        self, snapshot: PortfolioIntelligenceSnapshot
    ) -> None:
        """Record a snapshot into persistent history without duplicate timestamps."""
        try:
            if snapshot is None or not isinstance(snapshot, PortfolioIntelligenceSnapshot):
                return

            history = self.load_history()
            existing_ts = {s.timestamp for s in history}
            if snapshot.timestamp not in existing_ts:
                history.append(snapshot)
                self.save_history(history)
        except Exception:
            pass

    def get_history(self) -> list[PortfolioIntelligenceSnapshot]:
        """Retrieve stored history snapshots."""
        return self.load_history()

    def get_intelligence(
        self, portfolio_data: Optional[Any] = None
    ) -> PortfolioIntelligenceResult:
        """Collect current portfolio snapshot, record history, and return complete result."""
        try:
            current_snap = self.load_portfolio(portfolio_data)
            if current_snap.total_holdings > 0:
                self.record_snapshot(current_snap)

            history = self.load_history()

            summary = self.build_summary(current_snap)
            return PortfolioIntelligenceResult(
                summary=summary,
                snapshots=history,
            )
        except Exception:
            return _empty_result("UNAVAILABLE")
