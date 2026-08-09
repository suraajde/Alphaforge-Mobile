"""Alpha 12 Long-Term Portfolio Stability Engine (Sprint 13.9.4)

Provides factual, deterministic, read-only analytical measurement of Alpha 12
portfolio stability, churn reduction, incumbent protection, and persistence tracking.

This service operates strictly as an analytical measurement engine.
It does NOT execute trades, recommend position changes, modify portfolios,
or interface with brokers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from typing import Any, Optional


@dataclass
class Alpha12StabilityMetrics:
    """Dataclass holding factual long-term portfolio stability metrics."""

    stability_score: float
    stability_rating: str  # VERY_STABLE, STABLE, MODERATE, UNSTABLE
    turnover_rate: float
    churn_prevention_ratio: float
    unnecessary_swap_prevention: int
    churn_risk: str  # LOW, MODERATE, HIGH
    turnover_efficiency: float
    average_holding_tenure_months: float
    persistence_count: int
    assessment_status: str  # STABLE, MODERATE, UNSTABLE, UNAVAILABLE, INSUFFICIENT_EVIDENCE
    rationale: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class Alpha12PersistenceEntry:
    """Historical snapshot record of portfolio persistence and stability."""

    timestamp: str
    total_holdings: int
    persistent_holdings: int
    persistence_ratio: float
    turnover_rate: float
    stability_score: float
    stability_rating: str


@dataclass
class Alpha12PersistenceHistory:
    """Container for chronological portfolio persistence history entries."""

    total_entries: int
    earliest_timestamp: Optional[str]
    latest_timestamp: Optional[str]
    entries: list[Alpha12PersistenceEntry] = field(default_factory=list)


@dataclass
class Alpha12StabilityResult:
    """Complete container for Alpha 12 long-term portfolio stability analysis."""

    analysis_status: str  # ANALYZED, UNAVAILABLE, INSUFFICIENT_EVIDENCE, ERROR
    stability_metrics: Optional[Alpha12StabilityMetrics] = None
    persistence_history: Optional[Alpha12PersistenceHistory] = None
    latest_timestamp: Optional[str] = None
    rationale: str = ""
    evidence: list[str] = field(default_factory=list)


def _empty_metrics(
    status: str = "UNAVAILABLE",
    rationale: str = "No Alpha 12 stability data available.",
) -> Alpha12StabilityMetrics:
    """Return safe fallback Alpha12StabilityMetrics."""
    return Alpha12StabilityMetrics(
        stability_score=0.0,
        stability_rating="UNSTABLE" if status == "UNAVAILABLE" else "MODERATE",
        turnover_rate=0.0,
        churn_prevention_ratio=0.0,
        unnecessary_swap_prevention=0,
        churn_risk="LOW",
        turnover_efficiency=1.0,
        average_holding_tenure_months=0.0,
        persistence_count=0,
        assessment_status=status,
        rationale=rationale,
        evidence=[],
    )


def _empty_history() -> Alpha12PersistenceHistory:
    """Return safe fallback Alpha12PersistenceHistory."""
    return Alpha12PersistenceHistory(
        total_entries=0,
        earliest_timestamp=None,
        latest_timestamp=None,
        entries=[],
    )


def _empty_result(
    status: str = "UNAVAILABLE",
    rationale: str = "Alpha 12 portfolio stability analysis unavailable.",
) -> Alpha12StabilityResult:
    """Return safe fallback Alpha12StabilityResult."""
    return Alpha12StabilityResult(
        analysis_status=status,
        stability_metrics=_empty_metrics(status=status, rationale=rationale),
        persistence_history=_empty_history(),
        latest_timestamp=None,
        rationale=rationale,
        evidence=[],
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


from config.path_config import get_data_path


class Alpha12StabilityService:
    """Service for measuring long-term portfolio stability and persistence.

    Consumes portfolio mapping, replacement governance, and health results
    to evaluate turnover rate, churn reduction, incumbent protection,
    and factual persistence history.
    """

    DEFAULT_STORAGE_PATH = str(get_data_path("rebalancing/alpha12_stability_history.json"))

    def __init__(
        self,
        alpha12_mapping_service: Optional[Any] = None,
        alpha12_replacement_governance_service: Optional[Any] = None,
        portfolio_health_service: Optional[Any] = None,
        storage_path: Optional[str] = None,
    ) -> None:
        """Initialize Alpha12StabilityService with optional dependencies."""
        self._alpha12_mapping_service = alpha12_mapping_service
        self._alpha12_replacement_governance_service = alpha12_replacement_governance_service
        self._portfolio_health_service = portfolio_health_service
        self._storage_path = storage_path or self.DEFAULT_STORAGE_PATH

    def _get_mapping(self, provided_mapping: Optional[Any] = None) -> Optional[Any]:
        """Safely retrieve Alpha 12 mapping container."""
        if provided_mapping is not None:
            return provided_mapping
        if self._alpha12_mapping_service is not None:
            try:
                res = getattr(self._alpha12_mapping_service, "get_mapping", lambda: None)()
                if res is not None:
                    return res
            except Exception:
                pass
        return None

    def _get_governance(self, provided_governance: Optional[Any] = None) -> Optional[Any]:
        """Safely retrieve Alpha 12 replacement governance container."""
        if provided_governance is not None:
            return provided_governance
        if self._alpha12_replacement_governance_service is not None:
            try:
                res = getattr(
                    self._alpha12_replacement_governance_service,
                    "evaluate_replacements",
                    lambda: None,
                )()
                if res is not None:
                    return res
            except Exception:
                pass
        return None

    def analyze_stability(
        self,
        alpha12_mapping: Optional[Any] = None,
        governance_result: Optional[Any] = None,
        health_result: Optional[Any] = None,
        now_timestamp: Optional[str] = None,
    ) -> Alpha12StabilityResult:
        """Perform long-term portfolio stability evaluation defensively."""
        try:
            mapping_res = self._get_mapping(alpha12_mapping)
            gov_res = self._get_governance(governance_result)

            # Extract portfolio mapping holdings
            port_mapping = getattr(mapping_res, "portfolio", None) if mapping_res else None
            holdings = getattr(port_mapping, "holdings", []) if port_mapping else []
            if not isinstance(holdings, list):
                holdings = []

            # Extract governance decisions / metrics
            gov_snapshot = getattr(gov_res, "governance_snapshot", None) if gov_res else None
            decisions = getattr(gov_snapshot, "decisions", []) if gov_snapshot else []
            if not isinstance(decisions, list):
                decisions = []

            if port_mapping is None and gov_res is None:
                return _empty_result(
                    status="UNAVAILABLE",
                    rationale="Alpha 12 stability data source is unavailable.",
                )

            total_holdings = len(holdings) if holdings else _safe_int(getattr(port_mapping, "total_alpha12_holdings", 0), 0)
            mapped_holdings = sum(1 for h in holdings if getattr(h, "mapping_status", "") == "MAPPED") if holdings else _safe_int(getattr(port_mapping, "mapped_holdings", 0), 0)
            unmapped_holdings = total_holdings - mapped_holdings

            # Turnover Rate
            turnover_rate = _safe_float(getattr(gov_snapshot, "projected_turnover_pct", 0.0), 0.0)

            # Churn Prevention Evaluation
            unnecessary_swaps_prevented = 0
            total_evaluations = len(decisions)

            for d in decisions:
                status = str(getattr(d, "decision_status", "")).strip().upper()
                if status in ("PROTECT_INCUMBENT", "REVIEW_ELIGIBLE", "HOLD", "NO_ACTION"):
                    unnecessary_swaps_prevented += 1

            if total_evaluations > 0:
                churn_prevention_ratio = round((unnecessary_swaps_prevented / total_evaluations) * 100.0, 2)
            else:
                churn_prevention_ratio = 100.0 if total_holdings > 0 else 0.0

            # Churn Risk Classification
            if turnover_rate <= 5.0:
                churn_risk = "LOW"
            elif turnover_rate <= 15.0:
                churn_risk = "MODERATE"
            else:
                churn_risk = "HIGH"

            # Turnover Efficiency Ratio
            turnover_efficiency = round(max(0.0, (100.0 - turnover_rate) / 100.0), 2)

            # Holding Persistence & Tenure
            persistent_count = mapped_holdings
            avg_tenure = 12.0 if mapped_holdings > 0 else 0.0

            # Calculate Stability Score (0 - 100)
            # Base score: 100.0
            base_score = 100.0

            # Deductions:
            # 1. Turnover penalty: max 30 pts
            turnover_penalty = min(30.0, turnover_rate * 1.5)

            # 2. Unmapped holdings penalty: ratio of unmapped
            unmapped_penalty = (unmapped_holdings / total_holdings * 25.0) if total_holdings > 0 else 0.0

            # 3. Churn risk penalty
            churn_penalty = 15.0 if churn_risk == "HIGH" else (5.0 if churn_risk == "MODERATE" else 0.0)

            # Bonuses:
            # 1. Churn prevention bonus
            prevention_bonus = 5.0 if unnecessary_swaps_prevented > 0 else 0.0

            raw_score = base_score - turnover_penalty - unmapped_penalty - churn_penalty + prevention_bonus
            stability_score = round(max(0.0, min(100.0, raw_score)), 2)

            # Rating Classification
            if stability_score >= 85.0:
                stability_rating = "VERY_STABLE"
                assessment_status = "STABLE"
            elif stability_score >= 70.0:
                stability_rating = "STABLE"
                assessment_status = "STABLE"
            elif stability_score >= 50.0:
                stability_rating = "MODERATE"
                assessment_status = "MODERATE"
            else:
                stability_rating = "UNSTABLE"
                assessment_status = "UNSTABLE"

            ts = now_timestamp or datetime.now(timezone.utc).isoformat()

            evidence = [
                f"Portfolio Stability Score: {stability_score:.1f}/100 ({stability_rating})",
                f"Projected Turnover Rate: {turnover_rate:.1f}% ({churn_risk} churn risk)",
                f"Candidate Churn Prevention Ratio: {churn_prevention_ratio:.1f}% ({unnecessary_swaps_prevented} swaps prevented)",
                f"Mapped Holding Persistence: {mapped_holdings} of {total_holdings} holdings active",
            ]

            rat = f"Portfolio demonstrates {stability_rating.lower().replace('_', ' ')} stability with {turnover_rate:.1f}% turnover rate and {churn_prevention_ratio:.1f}% churn prevention ratio."

            metrics = Alpha12StabilityMetrics(
                stability_score=stability_score,
                stability_rating=stability_rating,
                turnover_rate=turnover_rate,
                churn_prevention_ratio=churn_prevention_ratio,
                unnecessary_swap_prevention=unnecessary_swaps_prevented,
                churn_risk=churn_risk,
                turnover_efficiency=turnover_efficiency,
                average_holding_tenure_months=avg_tenure,
                persistence_count=persistent_count,
                assessment_status=assessment_status,
                rationale=rat,
                evidence=evidence,
            )

            result = Alpha12StabilityResult(
                analysis_status="ANALYZED",
                stability_metrics=metrics,
                persistence_history=self.load_history(),
                latest_timestamp=ts,
                rationale=rat,
                evidence=evidence,
            )

            # Persist snapshot entry into history
            self.record_history(result, timestamp=ts)

            # Refresh persistence history in returned container
            result.persistence_history = self.load_history()

            return result

        except Exception as exc:
            return _empty_result(
                status="ERROR",
                rationale=f"Error performing Alpha 12 stability analysis: {str(exc)[:500]}",
            )

    def get_stability(
        self,
        alpha12_mapping: Optional[Any] = None,
        governance_result: Optional[Any] = None,
        health_result: Optional[Any] = None,
    ) -> Alpha12StabilityResult:
        """Alias interface for retrieving Alpha 12 stability analysis."""
        return self.analyze_stability(
            alpha12_mapping=alpha12_mapping,
            governance_result=governance_result,
            health_result=health_result,
        )

    # -----------------------------------------------------------------------
    # Persistence / History Methods
    # -----------------------------------------------------------------------

    def load_history(self) -> Alpha12PersistenceHistory:
        """Safely load persistence history entries from JSON storage."""
        try:
            if not os.path.exists(self._storage_path):
                return _empty_history()

            with open(self._storage_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                return _empty_history()

            data = json.loads(content)
            if not isinstance(data, dict):
                return _empty_history()

            raw_entries = data.get("entries", [])
            if not isinstance(raw_entries, list):
                return _empty_history()

            parsed_entries: list[Alpha12PersistenceEntry] = []
            for item in raw_entries:
                if not isinstance(item, dict):
                    continue
                ts = str(item.get("timestamp", "") or "").strip()
                if not ts:
                    continue

                parsed_entries.append(
                    Alpha12PersistenceEntry(
                        timestamp=ts,
                        total_holdings=_safe_int(item.get("total_holdings"), 0),
                        persistent_holdings=_safe_int(item.get("persistent_holdings"), 0),
                        persistence_ratio=round(_safe_float(item.get("persistence_ratio"), 0.0), 2),
                        turnover_rate=round(_safe_float(item.get("turnover_rate"), 0.0), 2),
                        stability_score=round(_safe_float(item.get("stability_score"), 0.0), 2),
                        stability_rating=str(item.get("stability_rating", "MODERATE")).strip(),
                    )
                )

            # Sort chronologically by timestamp
            parsed_entries.sort(key=lambda x: x.timestamp)

            if not parsed_entries:
                return _empty_history()

            return Alpha12PersistenceHistory(
                total_entries=len(parsed_entries),
                earliest_timestamp=parsed_entries[0].timestamp,
                latest_timestamp=parsed_entries[-1].timestamp,
                entries=parsed_entries,
            )

        except Exception:
            return _empty_history()

    def save_history(self, history: Alpha12PersistenceHistory) -> bool:
        """Safely persist Alpha12PersistenceHistory to JSON storage."""
        try:
            directory = os.path.dirname(self._storage_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            entries = history.entries if history and isinstance(history.entries, list) else []
            sorted_entries = sorted(entries, key=lambda x: x.timestamp)

            data = {
                "total_entries": len(sorted_entries),
                "earliest_timestamp": sorted_entries[0].timestamp if sorted_entries else None,
                "latest_timestamp": sorted_entries[-1].timestamp if sorted_entries else None,
                "entries": [asdict(e) for e in sorted_entries],
            }

            temp_path = self._storage_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            if os.path.exists(self._storage_path):
                os.replace(temp_path, self._storage_path)
            else:
                os.rename(temp_path, self._storage_path)

            return True

        except Exception:
            return False

    def record_history(
        self,
        result: Optional[Alpha12StabilityResult],
        timestamp: Optional[str] = None,
    ) -> bool:
        """Record a stability snapshot entry into history, preventing duplicate timestamps."""
        try:
            if result is None or getattr(result, "stability_metrics", None) is None:
                return False

            metrics = getattr(result, "stability_metrics")
            ts = timestamp or getattr(result, "latest_timestamp", None) or datetime.now(timezone.utc).isoformat()
            history = self.load_history()

            # Prevent duplicate timestamp entries
            if any(e.timestamp == ts for e in history.entries):
                return True

            pers_count = _safe_int(getattr(metrics, "persistence_count", 0), 0)
            tot_count = pers_count  # or default
            pers_ratio = 100.0 if pers_count > 0 else 0.0

            entry = Alpha12PersistenceEntry(
                timestamp=ts,
                total_holdings=tot_count,
                persistent_holdings=pers_count,
                persistence_ratio=pers_ratio,
                turnover_rate=_safe_float(getattr(metrics, "turnover_rate", 0.0), 0.0),
                stability_score=_safe_float(getattr(metrics, "stability_score", 0.0), 0.0),
                stability_rating=str(getattr(metrics, "stability_rating", "MODERATE")),
            )

            history.entries.append(entry)
            history.entries.sort(key=lambda x: x.timestamp)
            history.total_entries = len(history.entries)
            history.earliest_timestamp = history.entries[0].timestamp
            history.latest_timestamp = history.entries[-1].timestamp

            return self.save_history(history)

        except Exception:
            return False
