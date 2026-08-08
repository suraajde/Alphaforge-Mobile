from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

# Reuse existing DecisionPriority dataclass from prioritization service
try:
    from services.decision_prioritization_service import DecisionPriority
except ImportError:
    # Fallback stub if import fails during static analysis
    @dataclass
    class DecisionPriority:
        decision_id: str = ""
        category: str = ""
        priority: str = ""
        description: str = ""


@dataclass
class DecisionDashboardSummary:
    """Summary of aggregated decision engine, classification and prioritization results."""

    engine_status: str = "UNAVAILABLE"
    total_decisions: int = 0
    total_classifications: int = 0
    total_prioritized: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0


@dataclass
class DecisionDashboardResult:
    """Aggregated result for the Decision Dashboard UI."""

    summary: DecisionDashboardSummary
    priorities: List[DecisionPriority] = field(default_factory=list)


class DecisionDashboardService:
    """Service that builds a dashboard by aggregating Decision Engine, Classification and Prioritization.

    It does **not** implement any new decision logic – it simply composes existing results.
    All methods are defensive and never raise exceptions to the UI.
    """

    def __init__(
        self,
        decision_engine_service: Optional[Any] = None,
        decision_classification_service: Optional[Any] = None,
        decision_prioritization_service: Optional[Any] = None,
    ) -> None:
        self.decision_engine_service = decision_engine_service
        self.decision_classification_service = decision_classification_service
        self.decision_prioritization_service = decision_prioritization_service

    # ---------------------------------------------------------------------
    # Helper to safely extract counts from objects – defensive against None
    # ---------------------------------------------------------------------
    @staticmethod
    def _safe_int(val: Any, default: int = 0) -> int:
        try:
            return int(val)
        except Exception:
            return default

    # ---------------------------------------------------------------------
    # Build the summary dataclass
    # ---------------------------------------------------------------------
    def build_summary(
        self,
        decision_engine: Optional[Any] = None,
        classifications: Optional[Any] = None,
        prioritization: Optional[Any] = None,
    ) -> DecisionDashboardSummary:
        # Engine status & total decisions
        if decision_engine is not None and hasattr(decision_engine, "summary"):
            engine_status = getattr(decision_engine.summary, "engine_status", "UNAVAILABLE")
            total_decisions = self._safe_int(getattr(decision_engine.summary, "total_decisions", 0))
        else:
            engine_status = "UNAVAILABLE"
            total_decisions = 0

        # Classification totals
        total_classifications = (
            self._safe_int(getattr(classifications, "total_classifications", 0))
            if classifications is not None
            else 0
        )

        # Prioritization totals and counts
        if prioritization is not None:
            total_prioritized = self._safe_int(getattr(prioritization, "total_prioritized", 0))
            critical = self._safe_int(getattr(prioritization, "critical_count", 0))
            high = self._safe_int(getattr(prioritization, "high_count", 0))
            medium = self._safe_int(getattr(prioritization, "medium_count", 0))
            low = self._safe_int(getattr(prioritization, "low_count", 0))
            info = self._safe_int(getattr(prioritization, "info_count", 0))
        else:
            total_prioritized = critical = high = medium = low = info = 0

        return DecisionDashboardSummary(
            engine_status=engine_status,
            total_decisions=total_decisions,
            total_classifications=total_classifications,
            total_prioritized=total_prioritized,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            info_count=info,
        )

    # ---------------------------------------------------------------------
    # Build the full dashboard result
    # ---------------------------------------------------------------------
    def build_dashboard(
        self,
        decision_engine: Optional[Any] = None,
        classifications: Optional[Any] = None,
        prioritization: Optional[Any] = None,
    ) -> DecisionDashboardResult:
        # Resolve services lazily if not provided
        try:
            if decision_engine is None and self.decision_engine_service is not None:
                decision_engine = self.decision_engine_service.evaluate()
        except Exception:
            decision_engine = None
        try:
            if classifications is None and self.decision_classification_service is not None:
                classifications = self.decision_classification_service.classify()
        except Exception:
            classifications = None
        try:
            if prioritization is None and self.decision_prioritization_service is not None:
                prioritization = self.decision_prioritization_service.prioritize()
        except Exception:
            prioritization = None

        summary = self.build_summary(decision_engine, classifications, prioritization)

        # Extract ordered priority list – preserve required order
        priorities: List[DecisionPriority] = []
        if prioritization is not None:
            raw = getattr(prioritization, "priorities", [])
            order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
            try:
                priorities = sorted(
                    list(raw),
                    key=lambda p: order.get(getattr(p, "priority", "INFO").upper(), 5),
                )
            except Exception:
                priorities = list(raw)

        return DecisionDashboardResult(summary=summary, priorities=priorities)

    # ---------------------------------------------------------------------
    # Public accessor used by UI / services
    # ---------------------------------------------------------------------
    def get_dashboard(self) -> DecisionDashboardResult:
        """Convenient method that builds the dashboard using injected services.

        All exceptions are caught and result in a safe default dashboard.
        """
        try:
            return self.build_dashboard()
        except Exception:
            empty_summary = DecisionDashboardSummary()
            return DecisionDashboardResult(summary=empty_summary, priorities=[])
